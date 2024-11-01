import asyncio
import json
import uuid
from datetime import datetime
from typing import List
from typing import Union
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic import Field

app = FastAPI()

# Hebrew dummy text
hebrew_text = (
    "זהו טקסט דמה בעברית שנועד להמחיש את הזרמת הנתונים באופן מדורג.\n"
    "כאן אנו מוסיפים עוד כמה משפטים כדי ליצור קטע ארוך יותר שניתן להזרימו לממשק המשתמש.\n"
    "בנוסף, הקטע האחרון בזרימה מסומן כ'סיכום' להשלמת הדוגמה."
)

empty_text = (
  ""
)
# Generate fake request IDs dictionary
request_ids = {
    f"id{i}": {
        "report_id": f"report_{i}",
        "report_title": f"כתבה דוגמה {i}",
        "report_raw_text": f"{hebrew_text} קטע מספר {i}",
        "speaker_a": f"מרצה א {i}",
        "speaker_b": f"מרצה ב {i}",
        "report_tazak": f"תזק דוגמה {i}",
        "report_updated_date": datetime.now().isoformat()
    }
    for i in range(1, 6)  # Generate 5 example reports
}

chosen_request_ids = ["id1", "id2", "id3"]


# Pydantic model for request payload
class RequestData(BaseModel):
    query: str
    keywords: List[str]
    auth_token: str
    date_range: str
    session_id: str
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversations: List[str]
    return_empty: bool = False


class RequestReportId(RequestData):
    report_id: str  # Additional field to fetch specific report data


class LLMAnswerFeedback(RequestData):
    llm_answer: str
    is_relevant: bool


# Second feedback model
class SingleReportFeedback(RequestData):
    report_id: str
    is_relevant: bool
    report_title: str


async def fake_data_generator():
    used_request_ids = []
    lines = hebrew_text.split("\n")
    text_length = len(lines)

    for i, line in enumerate(lines):
        # Set section_name to "Conclusion" only for the last line
        section_name = "Conclusion" if i == text_length - 1 else "Summary"

        # Yield each character in the line individually
        for char in line:
            response_data = {
                "generated_response": char,
                "section_name": section_name
            }
            yield json.dumps(response_data) + "\n"  # No additional "\n" here
            await asyncio.sleep(0.07)

        # After each line, insert a generated link
        available_ids = [id for id in chosen_request_ids if id not in used_request_ids]
        if available_ids:
            generated_link_id = available_ids[0]  # Pick the next unused ID
            used_request_ids.append(generated_link_id)  # Mark this ID as used
        else:
            generated_link_id = None  # No IDs left to choose

        response_data = {
            "generated_link": generated_link_id,
            "section_name": section_name
        }
        yield json.dumps(response_data) + "\n"
        await asyncio.sleep(0.07)


@app.post("/run_chat_stream")
async def stream_data(request_data: RequestData):
    headers = {"Request-Ids": json.dumps(list(request_ids.keys())), "Query-Id": request_data.query_id}
    if request_data.return_empty:
        return StreamingResponse(iter([]), media_type="application/json", headers={})

    return StreamingResponse(fake_data_generator(), media_type="application/json", headers=headers)


@app.post("/get_report")
async def get_report(request_data: RequestData):
    report_id = request_data.report_id
    report_data = request_ids.get(report_id)

    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")

    return report_data


# Update post route to handle feedback submissions
@app.post("/submit_feedback")
async def submit_feedback(feedback: Union[LLMAnswerFeedback, SingleReportFeedback]):
    if isinstance(feedback, LLMAnswerFeedback):
        # Handle feedback for LLMAnswerFeedback
        return {
            "message": "LLM answer feedback received",
            "query": feedback.query,
            "is_relevant": feedback.is_relevant,
            "llm_answer": feedback.llm_answer
        }
    elif isinstance(feedback, SingleReportFeedback):
        # Handle feedback for SingleReportFeedback
        return {
            "message": "Single report feedback received",
            "query": feedback.query,
            "is_relevant": feedback.is_relevant,
            "report_id": feedback.report_id,
            "report_title": feedback.report_title
        }


# Update post route to handle feedback submissions
@app.get("/get_hapaks")
async def get_hapaks():
    return ['חפק1', 'חפק2', 'חפק3', 'חפק4', 'חפק5', 'חפק6', 'חפק7', 'חפק8', 'חפק9', 'חפק10']


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)