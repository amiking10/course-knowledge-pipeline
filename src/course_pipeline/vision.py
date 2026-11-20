"""Optional vision description draft generator; never promotes AI output to source fact."""
from __future__ import annotations
import base64
import os
from pathlib import Path
from .enrichment import validate_note


def draft_visual_note(source_id: str, page_no: int, png: Path, model: str,
                      client=None) -> dict:
    """Requires an explicitly configured model and API key; no silent requests."""
    if not source_id or page_no < 1 or not model:
        raise ValueError('source_id, positive page number, and model required')
    if client is None:
        if not os.environ.get('OPENAI_API_KEY'):
            raise RuntimeError('OPENAI_API_KEY not configured; cannot generate visual notes')
        from openai import OpenAI
        client=OpenAI()
    payload=base64.b64encode(Path(png).read_bytes()).decode('ascii')
    response=client.responses.create(
        model=model,
        input=[{'role':'user','content':[
            {'type':'input_text','text':
             'Describe only visible educational content in this lecture slide. '
             'Transcribe equations if fully legible. Distinguish uncertain or '
             'unreadable parts. Do not infer what the diagram ought to say. '
             'Answer as concise plain text. This is an unverified draft.'},
            {'type':'input_image','image_url':'data:image/png;base64,'+payload}
        ]}],
    )
    note={'source_id':source_id,'page_no':page_no,'kind':'figure',
          'content':response.output_text,'evidence':f'AI visual draft from {png.name}; verify against original',
          'reviewed':False,'model':model}
    validate_note(note)
    return note
