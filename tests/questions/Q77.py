import requests, json

question = "Calculate the baseline Asset Turnover ratio for the infrastructure asset expansion program in FY26 using the specific line items for 'Other Mfr. Exp' and 'Other Expenses' to determine manufacturing facility yield."

res = requests.post(
    "http://localhost:8000/api/v1/query",
    json={"question": question, "company_slug": "astral_ltd"}
)
print(json.dumps(res.json(), indent=2))