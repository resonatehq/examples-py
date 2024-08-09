import json
from collections.abc import Generator, Mapping
from typing import Any, Literal

import ollama
from resonate.context import Context
from resonate.typing import Yieldable


def _generate(
    ctx: Context, model: Literal["llama3.1"], prompt: str, seed: int | None
) -> Mapping[str, Any]:
    options: ollama.Options | None = None
    if seed is not None:
        options = ollama.Options(seed=seed)

    return ollama.generate(model=model, prompt=prompt, options=options)


def generate_a_joke(
    ctx: Context, seed: int | None = None
) -> Generator[Yieldable, Any, dict[str, Any]]:
    response = yield ctx.call(
        _generate,
        model="llama3.1",
        prompt='Please adhere to the following guidelines for all future responses: 1) You are a machine that only returns and replies with valid, iterable RFC8259 compliant JSON in your responses. 2) Do not include warnings, reminders, or explanations in your responses. 3) If no context for a question is provided, guess or assume the context of the topic based on the keywords provided. Do not respond saying that you need more context or information. 4) Your purpose is to generate business context details for technical column names that are being provided as keywords. 5) The response should be the Normalized (Human Readable / non-camel case) Name of the provided keyword..  --- The response must be returned in the following JSON format. [{"keyword": "The original keyword value", "context_response": " the Normalized (Human Readable / non-camel case) Name of the provided keyword"}, {"keyword": "The original keyword value", "context_response": " the Normalized (Human Readable / non-camel case) Name of the provided keyword"}] --- Provide appropriate values for each of the following keywords (in the following semicolon separated list) as best as possible. --- ApplicationStatusName; BankRoutingAccountNumber; BankAccountNumber; BankRoutingNumber; LandlordRegistrationBusinessPhoneNumberKey; TenantApplicationFutureRentAmount; LandlordToTenantApplicationReferenceNumberBankKey; TenantApplicationTypeNameKey; LandlordToTenantApplicationReferenceNumberEmailAddressKey; TenantApplicationReferenceNumberPhoneKey; LandlordRegistrationPrimaryContactEmailAddressKey; LandlordRegistrationReferenceNumberEmailAddressCount; TenantApplicationNameKey; RecordEffectiveEndTimestamp; TenantApplicationFutureUtilityAssistanceAmount; LandlordRegistrationReferenceNumberFullAddressKey; LandlordRegistrationReferenceNumberBankKey; TenantKey; TenantApplicationStatusKey; TenantApplicationPastDueUtilityAmount; LandlordRegistrationAddressKey; LandlordRegistrationPrimaryContactMobilePhoneNumberKey; TenantToLandlordApplicationReferenceNumberEmailAddressCount; LandlordRegistrationPrimaryContactAddressKey; LandlordRegistrationReferenceNumberPhoneKey',
        seed=seed,
    )
    return json.loads(response["response"])
