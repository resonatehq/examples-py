import prompt_checking
import resonate


def test_prompt() -> None:
    s = resonate.testing.dst(
        seeds=[1],
        mocks={
            prompt_checking.query_duckduckgo: prompt_checking.testing.mocks.query_duckduckgo,  # noqa: E501
        },
    )[0]
    s.deps.set("model", "llama3.1")
    s.add(prompt_checking.use_case, query="home depot news")
    assert (
        s.run()[0].result()
        == "Here's a summary of the latest news from The Home Depot:\n\n**Recent Announcements**\n\n* The Home Depot is spending $18.3 billion to buy SRS Distribution, a huge building-projects supplier.\n* The company will release its Q2 2024 earnings on Aug 13, 2024, with expected revenue of $43,375.69 million and earnings of $4.48 per share.\n\n**Previous Announcements**\n\n* The Home Depot reported sales and earnings decline for the first quarter of fiscal 2024.\n* The company announced a pending acquisition of SRS Distribution Inc. and a conference call to discuss its performance.\n* In March 2024, Home Depot will buy SRS Distribution, a materials provider for professionals, in a deal valued at approximately $18.25 billion including debt.\n\n**Recent Earnings Reports**\n\n* For Q1 2024, Home Depot's revenues fell 2% year-over-year (y-o-y) to $36.4 billion.\n* Comparable sales decreased 2.8% during the quarter.\n* In February 2023, Home Depot reported fourth quarter and fiscal 2022 results, with sales for the fourth quarter of fiscal 2022 were $35.8 billion.\n\n**Other News**\n\n* Henry County police are looking for a man who exposed himself to a woman in a Home Depot store.\n* A security guard separates a group of migrants after a tow truck driver attempted to tow a migrant's vehicle while they tried to get work in the Home Depot parking lot.\n* The Home Depot has been accused of discriminatory practices, including refusing to hire African American workers.\n\nThese are just some of the recent news and announcements from The Home Depot."  # noqa: E501
    )
