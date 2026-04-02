from typing import Optional
from pydantic import Field
from sarvam_tool import BaseTool, ToolOutput, tool_logging_decorator
from sarvam_app_stream import StateContext, encode_interaction_id
from sarvam_agents_sdk import OnStartInput, OnStartOutput, OnEndInput, OnEndOutput
from datetime import datetime
import logging
import os
import re
import httpx
import json
import time
import uuid

log_level = os.getenv("LOG_LEVEL", "WARNING")
logging.basicConfig(level=log_level)
logger = logging.getLogger("JustDial Bot")



async def on_start(on_start_input: OnStartInput) -> OnStartOutput:
    """
    Called once the call connects.

    Expected agent_variables (set by JD via Sarvam Instant Outbound API):
        jduid, buyer_city, buyer_area       – buyer identity
        searched_keyword                    – what the buyer searched
        product_name, product_id            – filled only when buyer exited from product page
        catname, ncatid, jdmart_id          – category context (may be empty)
        lead_id                             – JD ref_id / ObjectId
        env                                 – "development" | "production"
        page_type                           – e.g. "b2b_prsltpg"
        mobile_number                       – buyer mobile (masked)

    This function:
        1. Fills fallback defaults for any missing variables
        2. Determines search_term (product_name if available, else searched_keyword)
        3. Calls Search API to fetch qualification questions
        4. Stores specification_options / quantity_unit_options for the bot
        5. Stores raw questions with IDs in internal_variables for on_end
    """

    logger.info(f"OnStartInput: {on_start_input}")
    return OnStartOutput(
        agent_variables=agent_variables,
        internal_variables=internal_variables,
        user_information=on_start_input.user_information,
        authoring_config=authoring_config,
    )


async def on_end(
    on_end_input: OnEndInput, ccid: Optional[str] = None
) -> OnEndOutput:
    """
    Maps bot-collected agent_variables to the JD Callback payload.

    spec_ques_N is built by iterating the raw questions stored in
    internal_variables["jd_raw_questions"] and matching each question to
    its collected answer:
      – quantity-type  →  "{quantity} {quantity_unit}"
      – radio/freetext →  looked up by question text in agent_variables["specifications"]
                          (the bot stores answers as {question_text: answer})

    call_outcome is auto-derived from collected data if not already set:
      Approved  – product confirmed + all spec questions answered
      Enriched  – product confirmed + at least one spec answered
      Interested – product confirmed, no specs
      Could Not Confirm – product not confirmed
    """
    return OnEndOutput(
        agent_variables=agent_variables,
        internal_variables=internal_variables,
    )
