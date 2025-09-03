import asyncio
import httpx
from scrapy import Selector
from fastapi import FastAPI, Request
from datetime import datetime, timedelta
from urllib.parse import parse_qsl

app = FastAPI()

LOGIN_URL = "https://partner.elliemd.com/MemberToolsDotNet/Login/FirestormLogin.aspx"


async def login(username: str, password: str, session: httpx.AsyncClient):
    r = await session.get(LOGIN_URL)
    res = Selector(text=r.text)
    viewstate = res.css("#__VIEWSTATE::attr(value)").get()
    event_validation = res.css("#__EVENTVALIDATION::attr(value)").get()
    viewstate_gen = res.css("#__VIEWSTATEGENERATOR::attr(value)").get()

    payload = {
        "__LASTFOCUS": "",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstate_gen,
        "__EVENTVALIDATION": event_validation,
        "txtLostEmailAddress": "",
        "txtRPDealerURL": "",
        "txtRPDealerID": "",
        "txtDealerID": username,
        "Password": password,
        "cboCountry": "USA",
        "btnLogin": "Login",
    }

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://partner.elliemd.com",
        "referer": LOGIN_URL,
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
        ),
    }

    print("Logging in...")
    r = await session.post(LOGIN_URL, data=payload, headers=headers)
    if "FirestormLogin" in r.text or "Invalid" in r.text:
        print("❌ Login failed")
        return {"status": False, "html": r.text[:500]}

    print("✅ Login successful")
    return {"status": True, "cookies": session.cookies}

ORDER_HISTORY_URL = "https://partner.elliemd.com/MemberToolsDotNet/Reports/FirestormOrderHistoryV4.aspx"

async def fetch_listing(session: httpx.AsyncClient, customer_name: str):
    r = await session.get(ORDER_HISTORY_URL)
    sel = Selector(text=r.text)
    viewstate = sel.css("#__VIEWSTATE::attr(value)").get()
    viewstate_gen = sel.css("#__VIEWSTATEGENERATOR::attr(value)").get()
    event_validation = sel.css("#__EVENTVALIDATION::attr(value)").get()

    query = """Timeout_CountryID=USA&ctl00_RadScriptManager1_TSM=%3B%3BSystem.Web.Extensions%2C%20Version%3D4.0.0.0%2C%20Culture%3Dneutral%2C%20PublicKeyToken%3D31bf3856ad364e35%3Aen-US%3A95047a2c-8908-49e3-b68e-d249be89f134%3Aea597d4b%3Ab25378d2%3BTelerik.Web.UI%2C%20Version%3D2024.1.131.45%2C%20Culture%3Dneutral%2C%20PublicKeyToken%3D121fae78165ba3d4%3Aen-US%3A9948a144-ff46-44f4-9ae0-6f54d8eaff7b%3A16e4e7cd%3Aed16cbdc%3A4877f69a%3A33715776%3A86526ba7%3A874f8ea2%3Af7645509%3A24ee1bba%3Af46195d3%3A2003d0b8%3Ac128760b%3A88144a7a%3A1e771326%3Aaa288e2d%3Ab092aa46%3A7c926187%3A8674cba1%3Ab7778d6c%3Ac08e9f8a%3Aa51ee93e%3A59462f1%3A6d43f6d9%3Addbfcb67&__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwUKLTc0NTk4MzUwMQ9kFgJmDw8WBB4PX19BbnRpWHNyZlRva2VuBSA0MGMxMGQ0MWMyMDI0OTlhYjcxY2FhOGZiMmI1ZjNlYR4SX19BbnRpWHNyZlVzZXJOYW1lZWQWBGYPZBYKAggPFgIeBGhyZWYFH1N0eWxlcy5jc3M%2FdD02Mzg5MjI4OTI4NzQ4MTQzNDBkAgkPFgIfAgUjZnMtYW5pbWF0ZS5jc3M%2FdD02Mzg5MjI4OTI4NzQ4MTQzNDBkAgoPFgIfAgUgZnMtZ3JpZC5jc3M%2FdD02Mzg5MjI4OTI4NzQ4MTQzNDBkAgsPFgIfAgUgZnMtYmFzZS5jc3M%2FdD02Mzg5MjI4OTI4NzQ4MTQzNDBkAgwPFgIfAgUhZnMtdmlkZW8uY3NzP3Q9NjM4OTIyODkyODc0ODE0MzQwZAIBDxYCHgVjbGFzcwUqRmlyZXN0b3JtUGFnZV9GaXJlc3Rvcm1PcmRlckhpc3Rvcnl2NF9hc3B4FgICAQ9kFggCAw9kFgJmDxQrAAIPFgQeE2NhY2hlZFNlbGVjdGVkVmFsdWVkHgdWaXNpYmxlaGQQFhVmAgECAgIDAgQCBQIGAgcCCAIJAgoCCwIMAg0CDgIPAhACEQISAhMCFBYVFCsAAg8WBh4EVGV4dAUFQmxhY2seBVZhbHVlBQVCbGFjax4IU2VsZWN0ZWRoZGQUKwACDxYGHwYFD0JsYWNrTWV0cm9Ub3VjaB8HBQ9CbGFja01ldHJvVG91Y2gfCGhkZBQrAAIPFgYfBgUJQm9vdHN0cmFwHwcFCUJvb3RzdHJhcB8IaGRkFCsAAg8WBh8GBQdEZWZhdWx0HwcFB0RlZmF1bHQfCGdkZBQrAAIPFgYfBgUER2xvdx8HBQRHbG93HwhoZGQUKwACDxYGHwYFCE1hdGVyaWFsHwcFCE1hdGVyaWFsHwhoZGQUKwACDxYGHwYFBU1ldHJvHwcFBU1ldHJvHwhoZGQUKwACDxYGHwYFCk1ldHJvVG91Y2gfBwUKTWV0cm9Ub3VjaB8IaGRkFCsAAg8WBh8GBQpPZmZpY2UyMDA3HwcFCk9mZmljZTIwMDcfCGhkZBQrAAIPFgYfBgUPT2ZmaWNlMjAxMEJsYWNrHwcFD09mZmljZTIwMTBCbGFjax8IaGRkFCsAAg8WBh8GBQ5PZmZpY2UyMDEwQmx1ZR8HBQ5PZmZpY2UyMDEwQmx1ZR8IaGRkFCsAAg8WBh8GBRBPZmZpY2UyMDEwU2lsdmVyHwcFEE9mZmljZTIwMTBTaWx2ZXIfCGhkZBQrAAIPFgYfBgUHT3V0bG9vax8HBQdPdXRsb29rHwhoZGQUKwACDxYGHwYFBFNpbGsfBwUEU2lsax8IaGRkFCsAAg8WBh8GBQZTaW1wbGUfBwUGU2ltcGxlHwhoZGQUKwACDxYGHwYFBlN1bnNldB8HBQZTdW5zZXQfCGhkZBQrAAIPFgYfBgUHVGVsZXJpax8HBQdUZWxlcmlrHwhoZGQUKwACDxYGHwYFBVZpc3RhHwcFBVZpc3RhHwhoZGQUKwACDxYGHwYFBVdlYjIwHwcFBVdlYjIwHwhoZGQUKwACDxYGHwYFB1dlYkJsdWUfBwUHV2ViQmx1ZR8IaGRkFCsAAg8WBh8GBQhXaW5kb3dzNx8HBQhXaW5kb3dzNx8IaGRkDxYVZmZmZmZmZmZmZmZmZmZmZmZmZmZmFgEFd1RlbGVyaWsuV2ViLlVJLlJhZENvbWJvQm94SXRlbSwgVGVsZXJpay5XZWIuVUksIFZlcnNpb249MjAyNC4xLjEzMS40NSwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj0xMjFmYWU3ODE2NWJhM2Q0Fi5mDw8WBB4IQ3NzQ2xhc3MFCXJjYkhlYWRlch4EXyFTQgICZGQCAQ8PFgQfCQUJcmNiRm9vdGVyHwoCAmRkAgIPDxYGHwYFBUJsYWNrHwcFBUJsYWNrHwhoZGQCAw8PFgYfBgUPQmxhY2tNZXRyb1RvdWNoHwcFD0JsYWNrTWV0cm9Ub3VjaB8IaGRkAgQPDxYGHwYFCUJvb3RzdHJhcB8HBQlCb290c3RyYXAfCGhkZAIFDw8WBh8GBQdEZWZhdWx0HwcFB0RlZmF1bHQfCGdkZAIGDw8WBh8GBQRHbG93HwcFBEdsb3cfCGhkZAIHDw8WBh8GBQhNYXRlcmlhbB8HBQhNYXRlcmlhbB8IaGRkAggPDxYGHwYFBU1ldHJvHwcFBU1ldHJvHwhoZGQCCQ8PFgYfBgUKTWV0cm9Ub3VjaB8HBQpNZXRyb1RvdWNoHwhoZGQCCg8PFgYfBgUKT2ZmaWNlMjAwNx8HBQpPZmZpY2UyMDA3HwhoZGQCCw8PFgYfBgUPT2ZmaWNlMjAxMEJsYWNrHwcFD09mZmljZTIwMTBCbGFjax8IaGRkAgwPDxYGHwYFDk9mZmljZTIwMTBCbHVlHwcFDk9mZmljZTIwMTBCbHVlHwhoZGQCDQ8PFgYfBgUQT2ZmaWNlMjAxMFNpbHZlch8HBRBPZmZpY2UyMDEwU2lsdmVyHwhoZGQCDg8PFgYfBgUHT3V0bG9vax8HBQdPdXRsb29rHwhoZGQCDw8PFgYfBgUEU2lsax8HBQRTaWxrHwhoZGQCEA8PFgYfBgUGU2ltcGxlHwcFBlNpbXBsZR8IaGRkAhEPDxYGHwYFBlN1bnNldB8HBQZTdW5zZXQfCGhkZAISDw8WBh8GBQdUZWxlcmlrHwcFB1RlbGVyaWsfCGhkZAITDw8WBh8GBQVWaXN0YR8HBQVWaXN0YR8IaGRkAhQPDxYGHwYFBVdlYjIwHwcFBVdlYjIwHwhoZGQCFQ8PFgYfBgUHV2ViQmx1ZR8HBQdXZWJCbHVlHwhoZGQCFg8PFgYfBgUIV2luZG93czcfBwUIV2luZG93czcfCGhkZAIHDw8WCB4VRW5hYmxlRW1iZWRkZWRTY3JpcHRzZx4cRW5hYmxlRW1iZWRkZWRCYXNlU3R5bGVzaGVldGceElJlc29sdmVkUmVuZGVyTW9kZQspclRlbGVyaWsuV2ViLlVJLlJlbmRlck1vZGUsIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMjQuMS4xMzEuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNAEeF0VuYWJsZUFqYXhTa2luUmVuZGVyaW5naBYCHgVzdHlsZQUNZGlzcGxheTpub25lO2QCCQ8PFgIfBgUITGFuZ3VhZ2VkZAIVD2QWCgIBD2QWAmYPZBYEZg9kFgQCAQ8PFgIeCEltYWdlVXJsBRMvZnMtaW1hZ2VzL2xvZ28ucG5nZGQCAw8WAh8PBXxkaXNwbGF5Om5vbmU7IGZvbnQtc2l6ZTogMThweDtjb2xvcjogd2hpdGU7YmFja2dyb3VuZC1jb2xvcjpyZ2IoMTkyLCAxMCwgMTApO2JvcmRlci1yYWRpdXM6IDEwcHggMTBweCAwIDA7cGFkZGluZzogOHB4IDEwcHg7ZAICD2QWBAIBDw8WAh8GBUk8aDEgY2xhc3M9J3dlbGNvbWUnPldlbGNvbWUsIExlZSBBbm5lIDxzcGFuPkxldHMgR2V0IFN0YXJ0ZWQhPC9zcGFuPjwvaDE%2BZGQCAg8PFgIfBWhkZAIDD2QWAmYPZBYCAgEPFCsAAhQrAAIPFgIfBWhkZGRkAgUPFgIfBWdkAgcPFgIfBWgWBAIBDxQrAAIUKwACZGRkZAIDDxQrAAIUKwACZGRkZAIJD2QWBAIBDw8WAh8GBQ1PcmRlciBIaXN0b3J5ZGQCAw9kFigCAQ8UKwACDxYOHgVMYWJlbAUKT3JkZXIgVHlwZR8EZB8LZx8MZx8NCysEAh8OaB8GBQhQZXJzb25hbGQQFgJmAgEWAhQrAAIPFgYfBgUIUGVyc29uYWwfBwUBMR8IZ2RkFCsAAg8WBh8GBQhDdXN0b21lch8HBQEyHwhoZGQPFgJmZhYBBXdUZWxlcmlrLldlYi5VSS5SYWRDb21ib0JveEl0ZW0sIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMjQuMS4xMzEuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNBYIZg8PFgQfCQUJcmNiSGVhZGVyHwoCAmRkAgEPDxYEHwkFCXJjYkZvb3Rlch8KAgJkZAICDw8WBh8GBQhQZXJzb25hbB8HBQExHwhnZGQCAw8PFgYfBgUIQ3VzdG9tZXIfBwUBMh8IaGRkAgMPDxYKHgxTZWxlY3RlZERhdGUGAICSfuro3QgeEV9za2lwTU1WYWxpZGF0aW9uaB8LZx8MZx8NCysEAmQWBGYPFCsACA8WFB8RBQpTdGFydCBEYXRlHwYFEzIwMjUtMDktMDEtMDAtMDAtMDAeEUVuYWJsZUFyaWFTdXBwb3J0aB4NTGFiZWxDc3NDbGFzcwUHcmlMYWJlbB8OaB4EU2tpbgUFVmlzdGEfDGcfE2gfDQsrBAIfC2dkFgYeClJlc2l6ZU1vZGULKXJUZWxlcmlrLldlYi5VSS5SZXNpemVNb2RlLCBUZWxlcmlrLldlYi5VSSwgVmVyc2lvbj0yMDI0LjEuMTMxLjQ1LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPTEyMWZhZTc4MTY1YmEzZDQAHwkFEXJpVGV4dEJveCByaUhvdmVyHwoCAhYGHxcLKwUAHwkFEXJpVGV4dEJveCByaUVycm9yHwoCAhYGHxcLKwUAHwkFE3JpVGV4dEJveCByaUZvY3VzZWQfCgICFgQfCQUTcmlUZXh0Qm94IHJpRW5hYmxlZB8KAgIWBh8XCysFAB8JBRRyaVRleHRCb3ggcmlEaXNhYmxlZB8KAgIWBh8XCysFAB8JBRFyaVRleHRCb3ggcmlFbXB0eR8KAgIWBh8XCysFAB8JBRByaVRleHRCb3ggcmlSZWFkHwoCAmQCAg8UKwANDxYIBQ1TZWxlY3RlZERhdGVzDwWPAVRlbGVyaWsuV2ViLlVJLkNhbGVuZGFyLkNvbGxlY3Rpb25zLkRhdGVUaW1lQ29sbGVjdGlvbiwgVGVsZXJpay5XZWIuVUksIFZlcnNpb249MjAyNC4xLjEzMS40NSwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj0xMjFmYWU3ODE2NWJhM2Q0FCsAAAULU3BlY2lhbERheXMPBZIBVGVsZXJpay5XZWIuVUkuQ2FsZW5kYXIuQ29sbGVjdGlvbnMuQ2FsZW5kYXJEYXlDb2xsZWN0aW9uLCBUZWxlcmlrLldlYi5VSSwgVmVyc2lvbj0yMDI0LjEuMTMxLjQ1LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPTEyMWZhZTc4MTY1YmEzZDQUKwAABQ9SZW5kZXJJbnZpc2libGVnBRFFbmFibGVNdWx0aVNlbGVjdGgPFgwfC2cfDGcfFGgfFgUFVmlzdGEfDQsrBAIfDmhkZBYEHwkFC3JjTWFpblRhYmxlHwoCAhYEHwkFDHJjT3RoZXJNb250aB8KAgJkFgQfCQUKcmNTZWxlY3RlZB8KAgJkFgQfCQUKcmNEaXNhYmxlZB8KAgIWBB8JBQxyY091dE9mUmFuZ2UfCgICFgQfCQUJcmNXZWVrZW5kHwoCAhYEHwkFB3JjSG92ZXIfCgICFgQfCQUvUmFkQ2FsZW5kYXJNb250aFZpZXcgUmFkQ2FsZW5kYXJNb250aFZpZXdfVmlzdGEfCgICFgQfCQUJcmNWaWV3U2VsHwoCAmQCBQ8PFgofEgYAQI1MtP%2FdCB8TaB8LZx8MZx8NCysEAmQWBGYPFCsACA8WFB8RBQhFbmQgRGF0ZR8GBRMyMDI1LTA5LTMwLTAwLTAwLTAwHxRoHxUFB3JpTGFiZWwfDmgfFgUFVmlzdGEfDGcfE2gfDQsrBAIfC2dkFgYfFwsrBQAfCQURcmlUZXh0Qm94IHJpSG92ZXIfCgICFgYfFwsrBQAfCQURcmlUZXh0Qm94IHJpRXJyb3IfCgICFgYfFwsrBQAfCQUTcmlUZXh0Qm94IHJpRm9jdXNlZB8KAgIWBB8JBRNyaVRleHRCb3ggcmlFbmFibGVkHwoCAhYGHxcLKwUAHwkFFHJpVGV4dEJveCByaURpc2FibGVkHwoCAhYGHxcLKwUAHwkFEXJpVGV4dEJveCByaUVtcHR5HwoCAhYGHxcLKwUAHwkFEHJpVGV4dEJveCByaVJlYWQfCgICZAICDxQrAA0PFggFDVNlbGVjdGVkRGF0ZXMPBY8BVGVsZXJpay5XZWIuVUkuQ2FsZW5kYXIuQ29sbGVjdGlvbnMuRGF0ZVRpbWVDb2xsZWN0aW9uLCBUZWxlcmlrLldlYi5VSSwgVmVyc2lvbj0yMDI0LjEuMTMxLjQ1LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPTEyMWZhZTc4MTY1YmEzZDQUKwAABQtTcGVjaWFsRGF5cw8FkgFUZWxlcmlrLldlYi5VSS5DYWxlbmRhci5Db2xsZWN0aW9ucy5DYWxlbmRhckRheUNvbGxlY3Rpb24sIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMjQuMS4xMzEuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNBQrAAAFD1JlbmRlckludmlzaWJsZWcFEUVuYWJsZU11bHRpU2VsZWN0aA8WDB8LZx8MZx8UaB8WBQVWaXN0YR8NCysEAh8OaGRkFgQfCQULcmNNYWluVGFibGUfCgICFgQfCQUMcmNPdGhlck1vbnRoHwoCAmQWBB8JBQpyY1NlbGVjdGVkHwoCAmQWBB8JBQpyY0Rpc2FibGVkHwoCAhYEHwkFDHJjT3V0T2ZSYW5nZR8KAgIWBB8JBQlyY1dlZWtlbmQfCgICFgQfCQUHcmNIb3Zlch8KAgIWBB8JBS9SYWRDYWxlbmRhck1vbnRoVmlldyBSYWRDYWxlbmRhck1vbnRoVmlld19WaXN0YR8KAgIWBB8JBQlyY1ZpZXdTZWwfCgICZAIHDzwrAAUBAA8WCh8GBQdSZWZyZXNoHw5oHwxnHw0LKwQCHwtnZGQCCQ88KwAFAQAPFgweB0VuYWJsZWRoHwYFCERvd25sb2FkHw5oHwxnHw0LKwQCHwtnZGQCCw8PFgofBgUMVG90YWwgT3JkZXJzHwtnHwxnHw0LKwQBHw5oZGQCDQ8PFgofBgUBMB8LZx8MZx8NCysEAR8OaGRkAg8PDxYKHwYFH1JldGFpbCBUb3RhbCAoQ3VzdG9tZXIgUHJpY2luZykfC2cfDGcfDQsrBAEfDmhkZAIRDw8WCh8GBWZUaGlzIGFtb3VudCBkb2VzIG5vdCBpbmNsdWRlIGFueSB2b2x1bWUgZnJvbSBvcmRlcnMgb3Igb3JkZXIgZGV0YWlscyB0aGF0IGhhdmUgYmVlbiB2b2lkZWQgb3Igb24gaG9sZC4fC2cfDGcfDQsrBAEfDmhkZAITDw8WCh8GBQUkMC4wMB8LZx8MZx8NCysEAR8OaGRkAhUPDxYKHwYFJFJldGFpbCBUb3RhbCAoQnJhbmQgUGFydG5lciBQcmljaW5nKR8LZx8MZx8NCysEAR8OaGRkAhcPDxYKHwYFZlRoaXMgYW1vdW50IGRvZXMgbm90IGluY2x1ZGUgYW55IHZvbHVtZSBmcm9tIG9yZGVycyBvciBvcmRlciBkZXRhaWxzIHRoYXQgaGF2ZSBiZWVuIHZvaWRlZCBvciBvbiBob2xkLh8LZx8MZx8NCysEAR8OaGRkAhkPDxYKHwYFBSQwLjAwHwtnHwxnHw0LKwQBHw5oZGQCGw8PFgofBgUYQ29tbWlzc2lvbmFsIFZvbHVtZSAoQ1YpHwtnHwxnHw0LKwQBHw5oZGQCHQ8PFgofBgVmVGhpcyBhbW91bnQgZG9lcyBub3QgaW5jbHVkZSBhbnkgdm9sdW1lIGZyb20gb3JkZXJzIG9yIG9yZGVyIGRldGFpbHMgdGhhdCBoYXZlIGJlZW4gdm9pZGVkIG9yIG9uIGhvbGQuHwtnHwxnHw0LKwQBHw5oZGQCHw8PFgofBgUFJDAuMDAfC2cfDGcfDQsrBAEfDmhkZAIhDw8WCh8GBQlQU1YgVG90YWwfC2cfDGcfDQsrBAEfDmhkZAIjDw8WCh8GBWZUaGlzIGFtb3VudCBkb2VzIG5vdCBpbmNsdWRlIGFueSB2b2x1bWUgZnJvbSBvcmRlcnMgb3Igb3JkZXIgZGV0YWlscyB0aGF0IGhhdmUgYmVlbiB2b2lkZWQgb3Igb24gaG9sZC4fC2cfDGcfDQsrBAEfDmhkZAIlDw8WCh8GBQUkMC4wMB8LZx8MZx8NCysEAR8OaGRkAicPFCsABg8WDB4LXyFEYXRhQm91bmRnHwtnHw5oHwxnHgtfIUl0ZW1Db3VudGYfDQsrBAJkFCsAA2RkFCsAAhYCHhFJdGVtUGxhY2VIb2xkZXJJRAU3Y3RsMDBfTWFpbkNvbnRlbnRfbHN0T3JkZXJIaXN0b3J5X09yZGVySGlzdG9yeUNvbnRhaW5lcmQUKwADDwUGXyFEU0lDZg8FC18hSXRlbUNvdW50Zg8FCF8hUENvdW50ZGQWAh4CX2NmZGQYAwUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFhkFF2N0bDAwJFJhZEZvcm1EZWNvcmF0b3IxBSVjdGwwMCRNYWluQ29udGVudCRjYm9PcmRlckhpc3RvcnlUeXBlBR5jdGwwMCRNYWluQ29udGVudCRjYm9TdGFydERhdGUFJ2N0bDAwJE1haW5Db250ZW50JGNib1N0YXJ0RGF0ZSRjYWxlbmRhcgUnY3RsMDAkTWFpbkNvbnRlbnQkY2JvU3RhcnREYXRlJGNhbGVuZGFyBRxjdGwwMCRNYWluQ29udGVudCRjYm9FbmREYXRlBSVjdGwwMCRNYWluQ29udGVudCRjYm9FbmREYXRlJGNhbGVuZGFyBSVjdGwwMCRNYWluQ29udGVudCRjYm9FbmREYXRlJGNhbGVuZGFyBShjdGwwMCRNYWluQ29udGVudCRidG5PcmRlckhpc3RvcnlSZWZyZXNoBSljdGwwMCRNYWluQ29udGVudCRidG5PcmRlckhpc3RvcnlEb3dubG9hZAU0Y3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFRpdGxlT3JkZXJDb3VudAU0Y3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFZhbHVlT3JkZXJDb3VudAU1Y3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFRpdGxlUmV0YWlsVG90YWwFK2N0bDAwJE1haW5Db250ZW50JGxibFRvb2x0aXBTdGF0UmV0YWlsVG90YWwFNWN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRWYWx1ZVJldGFpbFRvdGFsBThjdGwwMCRNYWluQ29udGVudCRsYmxPcmRlckhpc3RvcnlTdGF0VGl0bGVXaG9sZXNhbGVUb3RhbAUuY3RsMDAkTWFpbkNvbnRlbnQkbGJsVG9vbHRpcFN0YXRXaG9sZXNhbGVUb3RhbAU4Y3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFZhbHVlV2hvbGVzYWxlVG90YWwFMGN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRUaXRsZVVwbGluZQUrY3RsMDAkTWFpbkNvbnRlbnQkbGJsVG9vbHRpcFN0YXRVcGxpbmVUb3RhbAUwY3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFZhbHVlVXBsaW5lBS1jdGwwMCRNYWluQ29udGVudCRsYmxPcmRlckhpc3RvcnlTdGF0VGl0bGVQU1YFKGN0bDAwJE1haW5Db250ZW50JGxibFRvb2x0aXBTdGF0UFNWVG90YWwFLWN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRWYWx1ZVBTVgUhY3RsMDAkTWFpbkNvbnRlbnQkbHN0T3JkZXJIaXN0b3J5BSVjdGwwMCRNYWluQ29udGVudCRjYm9PcmRlckhpc3RvcnlUeXBlDxQrAAIFCFBlcnNvbmFsBQExZAURY3RsMDAkU2tpbkNob29zZXIPFCsAAmUFB0RlZmF1bHRkvZCeosH5H%2B4TQCYzDgmB1IwM4l%2Fn6veprv0aRO03qrY%3D&__VIEWSTATEGENERATOR=2CBE0447&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=200&__EVENTVALIDATION=%2FwEdAAhzFG8uMqLK05Rf9bd5%2By1t%2FtMFhCET8bj78QUjm1aMzr%2Fm40leH0R5p2hdFFldrQEkbpf2Kczwydbvw%2BedIEgcpHQZAvtR7iyrOhadpU4raJ%2BHHf%2BRU4SxdzfEqCDloQNxu7WHhwuzDBI3rXx%2FsSNyK5Q%2BXyhFw1Q5hmMIpSETz%2Bh81VTPlgN02j8cNlS9u8c%2BSeWC93cDX2wNstzqXI%2BG&ctl00_RadFormDecorator1_ClientState=&ctl00%24MainContent%24cboOrderHistoryType=Customer&ctl00_MainContent_cboOrderHistoryType_ClientState=%7B%22logEntries%22%3A%5B%5D%2C%22value%22%3A%222%22%2C%22text%22%3A%22Customer%22%2C%22enabled%22%3Atrue%2C%22checkedIndices%22%3A%5B%5D%2C%22checkedItemsTextOverflows%22%3Afalse%7D&ctl00%24MainContent%24cboStartDate=2025-08-01&ctl00%24MainContent%24cboStartDate%24dateInput=8%2F1%2F2025&ctl00_MainContent_cboStartDate_calendar_SD=%5B%5B2025%2C8%2C1%5D%5D&ctl00_MainContent_cboStartDate_calendar_AD=%5B%5B1980%2C1%2C1%5D%2C%5B2099%2C12%2C30%5D%2C%5B2025%2C8%2C1%5D%5D&ctl00_MainContent_cboStartDate_dateInput_ClientState=%7B%22enabled%22%3Atrue%2C%22emptyMessage%22%3A%22%22%2C%22validationText%22%3A%222025-08-01-00-00-00%22%2C%22valueAsString%22%3A%222025-08-01-00-00-00%22%2C%22minDateStr%22%3A%221980-01-01-00-00-00%22%2C%22maxDateStr%22%3A%222099-12-31-00-00-00%22%2C%22lastSetTextBoxValue%22%3A%228%2F1%2F2025%22%7D&ctl00_MainContent_cboStartDate_ClientState=&ctl00%24MainContent%24cboEndDate=2025-09-30&ctl00%24MainContent%24cboEndDate%24dateInput=9%2F30%2F2025&ctl00_MainContent_cboEndDate_calendar_SD=%5B%5D&ctl00_MainContent_cboEndDate_calendar_AD=%5B%5B1980%2C1%2C1%5D%2C%5B2099%2C12%2C30%5D%2C%5B2025%2C9%2C1%5D%5D&ctl00_MainContent_cboEndDate_dateInput_ClientState=%7B%22enabled%22%3Atrue%2C%22emptyMessage%22%3A%22%22%2C%22validationText%22%3A%222025-09-30-00-00-00%22%2C%22valueAsString%22%3A%222025-09-30-00-00-00%22%2C%22minDateStr%22%3A%221980-01-01-00-00-00%22%2C%22maxDateStr%22%3A%222099-12-31-00-00-00%22%2C%22lastSetTextBoxValue%22%3A%229%2F30%2F2025%22%7D&ctl00_MainContent_cboEndDate_ClientState=&ctl00%24MainContent%24btnOrderHistoryRefresh=Refresh&ctl00_MainContent_btnOrderHistoryRefresh_ClientState=%7B%22text%22%3A%22Refresh%22%2C%22value%22%3A%22%22%2C%22checked%22%3Afalse%2C%22target%22%3A%22%22%2C%22navigateUrl%22%3A%22%22%2C%22commandName%22%3A%22%22%2C%22commandArgument%22%3A%22%22%2C%22autoPostBack%22%3Atrue%2C%22selectedToggleStateIndex%22%3A0%2C%22validationGroup%22%3Anull%2C%22readOnly%22%3Afalse%2C%22primary%22%3Afalse%2C%22enabled%22%3Atrue%7D&ctl00_MainContent_btnOrderHistoryDownload_ClientState=%7B%22text%22%3A%22Download%22%2C%22value%22%3A%22%22%2C%22checked%22%3Afalse%2C%22target%22%3A%22%22%2C%22navigateUrl%22%3A%22%22%2C%22commandName%22%3A%22%22%2C%22commandArgument%22%3A%22%22%2C%22autoPostBack%22%3Afalse%2C%22selectedToggleStateIndex%22%3A0%2C%22validationGroup%22%3Anull%2C%22readOnly%22%3Afalse%2C%22primary%22%3Afalse%2C%22enabled%22%3Afalse%7D&ctl00_MainContent_lstOrderHistory_ClientState="""  # your long string

    payload = dict(parse_qsl(query))
    payload.update({
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstate_gen,
        "__EVENTVALIDATION": event_validation
    })
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://partner.elliemd.com",
        "Referer": ORDER_HISTORY_URL,
        "User-Agent": "Mozilla/5.0",
    }

    r = await session.post(ORDER_HISTORY_URL, data=payload, headers=headers)

    if r.status_code != 200:
        return {"status": "Failed to fetch listing"}
    else:
        res = Selector(text=r.text)
        rows = res.xpath("//div[@class='fsOrderHistoryList']//div[contains(@class,'fsOrderRow')]")
        print(f"Total rows found: {len(rows)}")
        for row in rows:
            customer = row.xpath("./*[contains(@class,'fsOrderShipRecipient')]/span[contains(@id,'OrderStatValueShippingRecipient')]/text()").get('')
            if customer_name in customer:
                print(f"Found matching customer: {customer}")
                order_id = row.xpath("./*[contains(@class,'fsOrderNumber ')]//span/@orderid").get('')
                url = f"https://partner.elliemd.com/MemberToolsDotNet/Reports/FirestormOrderReceipt.aspx?OrderID={order_id}"
                r = await session.get(url)
                if r.status_code != 200:
                    return {"status": "Failed to fetch order details", "data": r.text}
                res = Selector(text=r.text)                
                return {
                    "status": r.status_code,
                    "order": { 
                        "order_id": order_id,
                        "order_data": res.xpath("//td[text()='Order Date:']/following-sibling::td/text()").get('').strip(),
                        "order_status": res.xpath("//td[text()='Order Status:']/following-sibling::td/text()").get('').strip()
                        },
                    "shipping_address": { 
                        "name":res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[1]").get('').strip(),
                        "street": res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[2]").get('').strip(),
                        "city/state/zip": res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[3]").get('').strip(),
                        "phone": res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[4]").get('').strip(),
                        "email": res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[5]").get('').strip()
                        },
                    "products": [ 
                        {
                            'product#': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[1]/text()").get('').strip(),
                            'description': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[2]/text()").get('').strip(),
                            'quantity': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[3]/text()").get('').strip(),
                            'commissionable': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[4]/text()").get('').strip(),
                            'line_total': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[5]/text()").get('').strip()
                        }
                        ],
                    "payment": {
                        'method': res.xpath("//*[contains(text(),'Payment Method')]/text()").get('').replace('Payment Method:', '').strip(), 
                        }
                }
        return {"status": "No matching customer found"}

def get_yesterday_formatted():
    yesterday = datetime.now() - timedelta(days=1)
    year = yesterday.year
    month = yesterday.month
    day = yesterday.day
    return {
        'date_iso': yesterday.strftime('%Y-%m-%d'),
        'date_mdY': f"{month}/{day}/{year}",
        'date_full': f"{yesterday.strftime('%Y-%m-%d')}-00-00-00"
    }

async def fetch_last_listing(session: httpx.AsyncClient):
    r = await session.get(ORDER_HISTORY_URL)
    sel = Selector(text=r.text)
    viewstate = sel.css("#__VIEWSTATE::attr(value)").get()
    viewstate_gen = sel.css("#__VIEWSTATEGENERATOR::attr(value)").get()
    event_validation = sel.css("#__EVENTVALIDATION::attr(value)").get()
    from urllib.parse import parse_qsl

    query = """Timeout_CountryID=USA&ctl00_RadScriptManager1_TSM=%3B%3BSystem.Web.Extensions%2C%20Version%3D4.0.0.0%2C%20Culture%3Dneutral%2C%20PublicKeyToken%3D31bf3856ad364e35%3Aen-US%3A95047a2c-8908-49e3-b68e-d249be89f134%3Aea597d4b%3Ab25378d2%3BTelerik.Web.UI%2C%20Version%3D2024.1.131.45%2C%20Culture%3Dneutral%2C%20PublicKeyToken%3D121fae78165ba3d4%3Aen-US%3A9948a144-ff46-44f4-9ae0-6f54d8eaff7b%3A16e4e7cd%3Aed16cbdc%3A4877f69a%3A33715776%3A86526ba7%3A874f8ea2%3Af7645509%3A24ee1bba%3Af46195d3%3A2003d0b8%3Ac128760b%3A88144a7a%3A1e771326%3Aaa288e2d%3Ab092aa46%3A7c926187%3A8674cba1%3Ab7778d6c%3Ac08e9f8a%3Aa51ee93e%3A59462f1%3A6d43f6d9%3Addbfcb67&__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwUKLTc0NTk4MzUwMQ9kFgJmDw8WBB4PX19BbnRpWHNyZlRva2VuBSA0MGMxMGQ0MWMyMDI0OTlhYjcxY2FhOGZiMmI1ZjNlYR4SX19BbnRpWHNyZlVzZXJOYW1lZWQWBGYPZBYKAggPFgIeBGhyZWYFH1N0eWxlcy5jc3M%2FdD02Mzg5MjI4OTI4NzQ4MTQzNDBkAgkPFgIfAgUjZnMtYW5pbWF0ZS5jc3M%2FdD02Mzg5MjI4OTI4NzQ4MTQzNDBkAgoPFgIfAgUgZnMtZ3JpZC5jc3M%2FdD02Mzg5MjI4OTI4NzQ4MTQzNDBkAgsPFgIfAgUgZnMtYmFzZS5jc3M%2FdD02Mzg5MjI4OTI4NzQ4MTQzNDBkAgwPFgIfAgUhZnMtdmlkZW8uY3NzP3Q9NjM4OTIyODkyODc0ODE0MzQwZAIBDxYCHgVjbGFzcwUqRmlyZXN0b3JtUGFnZV9GaXJlc3Rvcm1PcmRlckhpc3Rvcnl2NF9hc3B4FgICAQ9kFggCAw9kFgJmDxQrAAIPFgQeE2NhY2hlZFNlbGVjdGVkVmFsdWVkHgdWaXNpYmxlaGQQFhVmAgECAgIDAgQCBQIGAgcCCAIJAgoCCwIMAg0CDgIPAhACEQISAhMCFBYVFCsAAg8WBh4EVGV4dAUFQmxhY2seBVZhbHVlBQVCbGFjax4IU2VsZWN0ZWRoZGQUKwACDxYGHwYFD0JsYWNrTWV0cm9Ub3VjaB8HBQ9CbGFja01ldHJvVG91Y2gfCGhkZBQrAAIPFgYfBgUJQm9vdHN0cmFwHwcFCUJvb3RzdHJhcB8IaGRkFCsAAg8WBh8GBQdEZWZhdWx0HwcFB0RlZmF1bHQfCGdkZBQrAAIPFgYfBgUER2xvdx8HBQRHbG93HwhoZGQUKwACDxYGHwYFCE1hdGVyaWFsHwcFCE1hdGVyaWFsHwhoZGQUKwACDxYGHwYFBU1ldHJvHwcFBU1ldHJvHwhoZGQUKwACDxYGHwYFCk1ldHJvVG91Y2gfBwUKTWV0cm9Ub3VjaB8IaGRkFCsAAg8WBh8GBQpPZmZpY2UyMDA3HwcFCk9mZmljZTIwMDcfCGhkZBQrAAIPFgYfBgUPT2ZmaWNlMjAxMEJsYWNrHwcFD09mZmljZTIwMTBCbGFjax8IaGRkFCsAAg8WBh8GBQ5PZmZpY2UyMDEwQmx1ZR8HBQ5PZmZpY2UyMDEwQmx1ZR8IaGRkFCsAAg8WBh8GBRBPZmZpY2UyMDEwU2lsdmVyHwcFEE9mZmljZTIwMTBTaWx2ZXIfCGhkZBQrAAIPFgYfBgUHT3V0bG9vax8HBQdPdXRsb29rHwhoZGQUKwACDxYGHwYFBFNpbGsfBwUEU2lsax8IaGRkFCsAAg8WBh8GBQZTaW1wbGUfBwUGU2ltcGxlHwhoZGQUKwACDxYGHwYFBlN1bnNldB8HBQZTdW5zZXQfCGhkZBQrAAIPFgYfBgUHVGVsZXJpax8HBQdUZWxlcmlrHwhoZGQUKwACDxYGHwYFBVZpc3RhHwcFBVZpc3RhHwhoZGQUKwACDxYGHwYFBVdlYjIwHwcFBVdlYjIwHwhoZGQUKwACDxYGHwYFB1dlYkJsdWUfBwUHV2ViQmx1ZR8IaGRkFCsAAg8WBh8GBQhXaW5kb3dzNx8HBQhXaW5kb3dzNx8IaGRkDxYVZmZmZmZmZmZmZmZmZmZmZmZmZmZmFgEFd1RlbGVyaWsuV2ViLlVJLlJhZENvbWJvQm94SXRlbSwgVGVsZXJpay5XZWIuVUksIFZlcnNpb249MjAyNC4xLjEzMS40NSwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj0xMjFmYWU3ODE2NWJhM2Q0Fi5mDw8WBB4IQ3NzQ2xhc3MFCXJjYkhlYWRlch4EXyFTQgICZGQCAQ8PFgQfCQUJcmNiRm9vdGVyHwoCAmRkAgIPDxYGHwYFBUJsYWNrHwcFBUJsYWNrHwhoZGQCAw8PFgYfBgUPQmxhY2tNZXRyb1RvdWNoHwcFD0JsYWNrTWV0cm9Ub3VjaB8IaGRkAgQPDxYGHwYFCUJvb3RzdHJhcB8HBQlCb290c3RyYXAfCGhkZAIFDw8WBh8GBQdEZWZhdWx0HwcFB0RlZmF1bHQfCGdkZAIGDw8WBh8GBQRHbG93HwcFBEdsb3cfCGhkZAIHDw8WBh8GBQhNYXRlcmlhbB8HBQhNYXRlcmlhbB8IaGRkAggPDxYGHwYFBU1ldHJvHwcFBU1ldHJvHwhoZGQCCQ8PFgYfBgUKTWV0cm9Ub3VjaB8HBQpNZXRyb1RvdWNoHwhoZGQCCg8PFgYfBgUKT2ZmaWNlMjAwNx8HBQpPZmZpY2UyMDA3HwhoZGQCCw8PFgYfBgUPT2ZmaWNlMjAxMEJsYWNrHwcFD09mZmljZTIwMTBCbGFjax8IaGRkAgwPDxYGHwYFDk9mZmljZTIwMTBCbHVlHwcFDk9mZmljZTIwMTBCbHVlHwhoZGQCDQ8PFgYfBgUQT2ZmaWNlMjAxMFNpbHZlch8HBRBPZmZpY2UyMDEwU2lsdmVyHwhoZGQCDg8PFgYfBgUHT3V0bG9vax8HBQdPdXRsb29rHwhoZGQCDw8PFgYfBgUEU2lsax8HBQRTaWxrHwhoZGQCEA8PFgYfBgUGU2ltcGxlHwcFBlNpbXBsZR8IaGRkAhEPDxYGHwYFBlN1bnNldB8HBQZTdW5zZXQfCGhkZAISDw8WBh8GBQdUZWxlcmlrHwcFB1RlbGVyaWsfCGhkZAITDw8WBh8GBQVWaXN0YR8HBQVWaXN0YR8IaGRkAhQPDxYGHwYFBVdlYjIwHwcFBVdlYjIwHwhoZGQCFQ8PFgYfBgUHV2ViQmx1ZR8HBQdXZWJCbHVlHwhoZGQCFg8PFgYfBgUIV2luZG93czcfBwUIV2luZG93czcfCGhkZAIHDw8WCB4VRW5hYmxlRW1iZWRkZWRTY3JpcHRzZx4cRW5hYmxlRW1iZWRkZWRCYXNlU3R5bGVzaGVldGceElJlc29sdmVkUmVuZGVyTW9kZQspclRlbGVyaWsuV2ViLlVJLlJlbmRlck1vZGUsIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMjQuMS4xMzEuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNAEeF0VuYWJsZUFqYXhTa2luUmVuZGVyaW5naBYCHgVzdHlsZQUNZGlzcGxheTpub25lO2QCCQ8PFgIfBgUITGFuZ3VhZ2VkZAIVD2QWCgIBD2QWAmYPZBYEZg9kFgQCAQ8PFgIeCEltYWdlVXJsBRMvZnMtaW1hZ2VzL2xvZ28ucG5nZGQCAw8WAh8PBXxkaXNwbGF5Om5vbmU7IGZvbnQtc2l6ZTogMThweDtjb2xvcjogd2hpdGU7YmFja2dyb3VuZC1jb2xvcjpyZ2IoMTkyLCAxMCwgMTApO2JvcmRlci1yYWRpdXM6IDEwcHggMTBweCAwIDA7cGFkZGluZzogOHB4IDEwcHg7ZAICD2QWBAIBDw8WAh8GBUk8aDEgY2xhc3M9J3dlbGNvbWUnPldlbGNvbWUsIExlZSBBbm5lIDxzcGFuPkxldHMgR2V0IFN0YXJ0ZWQhPC9zcGFuPjwvaDE%2BZGQCAg8PFgIfBWhkZAIDD2QWAmYPZBYCAgEPFCsAAhQrAAIPFgIfBWhkZGRkAgUPFgIfBWdkAgcPFgIfBWgWBAIBDxQrAAIUKwACZGRkZAIDDxQrAAIUKwACZGRkZAIJD2QWBAIBDw8WAh8GBQ1PcmRlciBIaXN0b3J5ZGQCAw9kFigCAQ8UKwACDxYOHgVMYWJlbAUKT3JkZXIgVHlwZR8EZB8LZx8MZx8NCysEAh8OaB8GBQhQZXJzb25hbGQQFgJmAgEWAhQrAAIPFgYfBgUIUGVyc29uYWwfBwUBMR8IZ2RkFCsAAg8WBh8GBQhDdXN0b21lch8HBQEyHwhoZGQPFgJmZhYBBXdUZWxlcmlrLldlYi5VSS5SYWRDb21ib0JveEl0ZW0sIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMjQuMS4xMzEuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNBYIZg8PFgQfCQUJcmNiSGVhZGVyHwoCAmRkAgEPDxYEHwkFCXJjYkZvb3Rlch8KAgJkZAICDw8WBh8GBQhQZXJzb25hbB8HBQExHwhnZGQCAw8PFgYfBgUIQ3VzdG9tZXIfBwUBMh8IaGRkAgMPDxYKHgxTZWxlY3RlZERhdGUGAICSfuro3QgeEV9za2lwTU1WYWxpZGF0aW9uaB8LZx8MZx8NCysEAmQWBGYPFCsACA8WFB8RBQpTdGFydCBEYXRlHwYFEzIwMjUtMDktMDEtMDAtMDAtMDAeEUVuYWJsZUFyaWFTdXBwb3J0aB4NTGFiZWxDc3NDbGFzcwUHcmlMYWJlbB8OaB4EU2tpbgUFVmlzdGEfDGcfE2gfDQsrBAIfC2dkFgYeClJlc2l6ZU1vZGULKXJUZWxlcmlrLldlYi5VSS5SZXNpemVNb2RlLCBUZWxlcmlrLldlYi5VSSwgVmVyc2lvbj0yMDI0LjEuMTMxLjQ1LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPTEyMWZhZTc4MTY1YmEzZDQAHwkFEXJpVGV4dEJveCByaUhvdmVyHwoCAhYGHxcLKwUAHwkFEXJpVGV4dEJveCByaUVycm9yHwoCAhYGHxcLKwUAHwkFE3JpVGV4dEJveCByaUZvY3VzZWQfCgICFgQfCQUTcmlUZXh0Qm94IHJpRW5hYmxlZB8KAgIWBh8XCysFAB8JBRRyaVRleHRCb3ggcmlEaXNhYmxlZB8KAgIWBh8XCysFAB8JBRFyaVRleHRCb3ggcmlFbXB0eR8KAgIWBh8XCysFAB8JBRByaVRleHRCb3ggcmlSZWFkHwoCAmQCAg8UKwANDxYIBQ1TZWxlY3RlZERhdGVzDwWPAVRlbGVyaWsuV2ViLlVJLkNhbGVuZGFyLkNvbGxlY3Rpb25zLkRhdGVUaW1lQ29sbGVjdGlvbiwgVGVsZXJpay5XZWIuVUksIFZlcnNpb249MjAyNC4xLjEzMS40NSwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj0xMjFmYWU3ODE2NWJhM2Q0FCsAAAULU3BlY2lhbERheXMPBZIBVGVsZXJpay5XZWIuVUkuQ2FsZW5kYXIuQ29sbGVjdGlvbnMuQ2FsZW5kYXJEYXlDb2xsZWN0aW9uLCBUZWxlcmlrLldlYi5VSSwgVmVyc2lvbj0yMDI0LjEuMTMxLjQ1LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPTEyMWZhZTc4MTY1YmEzZDQUKwAABQ9SZW5kZXJJbnZpc2libGVnBRFFbmFibGVNdWx0aVNlbGVjdGgPFgwfC2cfDGcfFGgfFgUFVmlzdGEfDQsrBAIfDmhkZBYEHwkFC3JjTWFpblRhYmxlHwoCAhYEHwkFDHJjT3RoZXJNb250aB8KAgJkFgQfCQUKcmNTZWxlY3RlZB8KAgJkFgQfCQUKcmNEaXNhYmxlZB8KAgIWBB8JBQxyY091dE9mUmFuZ2UfCgICFgQfCQUJcmNXZWVrZW5kHwoCAhYEHwkFB3JjSG92ZXIfCgICFgQfCQUvUmFkQ2FsZW5kYXJNb250aFZpZXcgUmFkQ2FsZW5kYXJNb250aFZpZXdfVmlzdGEfCgICFgQfCQUJcmNWaWV3U2VsHwoCAmQCBQ8PFgofEgYAQI1MtP%2FdCB8TaB8LZx8MZx8NCysEAmQWBGYPFCsACA8WFB8RBQhFbmQgRGF0ZR8GBRMyMDI1LTA5LTMwLTAwLTAwLTAwHxRoHxUFB3JpTGFiZWwfDmgfFgUFVmlzdGEfDGcfE2gfDQsrBAIfC2dkFgYfFwsrBQAfCQURcmlUZXh0Qm94IHJpSG92ZXIfCgICFgYfFwsrBQAfCQURcmlUZXh0Qm94IHJpRXJyb3IfCgICFgYfFwsrBQAfCQUTcmlUZXh0Qm94IHJpRm9jdXNlZB8KAgIWBB8JBRNyaVRleHRCb3ggcmlFbmFibGVkHwoCAhYGHxcLKwUAHwkFFHJpVGV4dEJveCByaURpc2FibGVkHwoCAhYGHxcLKwUAHwkFEXJpVGV4dEJveCByaUVtcHR5HwoCAhYGHxcLKwUAHwkFEHJpVGV4dEJveCByaVJlYWQfCgICZAICDxQrAA0PFggFDVNlbGVjdGVkRGF0ZXMPBY8BVGVsZXJpay5XZWIuVUkuQ2FsZW5kYXIuQ29sbGVjdGlvbnMuRGF0ZVRpbWVDb2xsZWN0aW9uLCBUZWxlcmlrLldlYi5VSSwgVmVyc2lvbj0yMDI0LjEuMTMxLjQ1LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPTEyMWZhZTc4MTY1YmEzZDQUKwAABQtTcGVjaWFsRGF5cw8FkgFUZWxlcmlrLldlYi5VSS5DYWxlbmRhci5Db2xsZWN0aW9ucy5DYWxlbmRhckRheUNvbGxlY3Rpb24sIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMjQuMS4xMzEuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNBQrAAAFD1JlbmRlckludmlzaWJsZWcFEUVuYWJsZU11bHRpU2VsZWN0aA8WDB8LZx8MZx8UaB8WBQVWaXN0YR8NCysEAh8OaGRkFgQfCQULcmNNYWluVGFibGUfCgICFgQfCQUMcmNPdGhlck1vbnRoHwoCAmQWBB8JBQpyY1NlbGVjdGVkHwoCAmQWBB8JBQpyY0Rpc2FibGVkHwoCAhYEHwkFDHJjT3V0T2ZSYW5nZR8KAgIWBB8JBQlyY1dlZWtlbmQfCgICFgQfCQUHcmNIb3Zlch8KAgIWBB8JBS9SYWRDYWxlbmRhck1vbnRoVmlldyBSYWRDYWxlbmRhck1vbnRoVmlld19WaXN0YR8KAgIWBB8JBQlyY1ZpZXdTZWwfCgICZAIHDzwrAAUBAA8WCh8GBQdSZWZyZXNoHw5oHwxnHw0LKwQCHwtnZGQCCQ88KwAFAQAPFgweB0VuYWJsZWRoHwYFCERvd25sb2FkHw5oHwxnHw0LKwQCHwtnZGQCCw8PFgofBgUMVG90YWwgT3JkZXJzHwtnHwxnHw0LKwQBHw5oZGQCDQ8PFgofBgUBMB8LZx8MZx8NCysEAR8OaGRkAg8PDxYKHwYFH1JldGFpbCBUb3RhbCAoQ3VzdG9tZXIgUHJpY2luZykfC2cfDGcfDQsrBAEfDmhkZAIRDw8WCh8GBWZUaGlzIGFtb3VudCBkb2VzIG5vdCBpbmNsdWRlIGFueSB2b2x1bWUgZnJvbSBvcmRlcnMgb3Igb3JkZXIgZGV0YWlscyB0aGF0IGhhdmUgYmVlbiB2b2lkZWQgb3Igb24gaG9sZC4fC2cfDGcfDQsrBAEfDmhkZAITDw8WCh8GBQUkMC4wMB8LZx8MZx8NCysEAR8OaGRkAhUPDxYKHwYFJFJldGFpbCBUb3RhbCAoQnJhbmQgUGFydG5lciBQcmljaW5nKR8LZx8MZx8NCysEAR8OaGRkAhcPDxYKHwYFZlRoaXMgYW1vdW50IGRvZXMgbm90IGluY2x1ZGUgYW55IHZvbHVtZSBmcm9tIG9yZGVycyBvciBvcmRlciBkZXRhaWxzIHRoYXQgaGF2ZSBiZWVuIHZvaWRlZCBvciBvbiBob2xkLh8LZx8MZx8NCysEAR8OaGRkAhkPDxYKHwYFBSQwLjAwHwtnHwxnHw0LKwQBHw5oZGQCGw8PFgofBgUYQ29tbWlzc2lvbmFsIFZvbHVtZSAoQ1YpHwtnHwxnHw0LKwQBHw5oZGQCHQ8PFgofBgVmVGhpcyBhbW91bnQgZG9lcyBub3QgaW5jbHVkZSBhbnkgdm9sdW1lIGZyb20gb3JkZXJzIG9yIG9yZGVyIGRldGFpbHMgdGhhdCBoYXZlIGJlZW4gdm9pZGVkIG9yIG9uIGhvbGQuHwtnHwxnHw0LKwQBHw5oZGQCHw8PFgofBgUFJDAuMDAfC2cfDGcfDQsrBAEfDmhkZAIhDw8WCh8GBQlQU1YgVG90YWwfC2cfDGcfDQsrBAEfDmhkZAIjDw8WCh8GBWZUaGlzIGFtb3VudCBkb2VzIG5vdCBpbmNsdWRlIGFueSB2b2x1bWUgZnJvbSBvcmRlcnMgb3Igb3JkZXIgZGV0YWlscyB0aGF0IGhhdmUgYmVlbiB2b2lkZWQgb3Igb24gaG9sZC4fC2cfDGcfDQsrBAEfDmhkZAIlDw8WCh8GBQUkMC4wMB8LZx8MZx8NCysEAR8OaGRkAicPFCsABg8WDB4LXyFEYXRhQm91bmRnHwtnHw5oHwxnHgtfIUl0ZW1Db3VudGYfDQsrBAJkFCsAA2RkFCsAAhYCHhFJdGVtUGxhY2VIb2xkZXJJRAU3Y3RsMDBfTWFpbkNvbnRlbnRfbHN0T3JkZXJIaXN0b3J5X09yZGVySGlzdG9yeUNvbnRhaW5lcmQUKwADDwUGXyFEU0lDZg8FC18hSXRlbUNvdW50Zg8FCF8hUENvdW50ZGQWAh4CX2NmZGQYAwUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFhkFF2N0bDAwJFJhZEZvcm1EZWNvcmF0b3IxBSVjdGwwMCRNYWluQ29udGVudCRjYm9PcmRlckhpc3RvcnlUeXBlBR5jdGwwMCRNYWluQ29udGVudCRjYm9TdGFydERhdGUFJ2N0bDAwJE1haW5Db250ZW50JGNib1N0YXJ0RGF0ZSRjYWxlbmRhcgUnY3RsMDAkTWFpbkNvbnRlbnQkY2JvU3RhcnREYXRlJGNhbGVuZGFyBRxjdGwwMCRNYWluQ29udGVudCRjYm9FbmREYXRlBSVjdGwwMCRNYWluQ29udGVudCRjYm9FbmREYXRlJGNhbGVuZGFyBSVjdGwwMCRNYWluQ29udGVudCRjYm9FbmREYXRlJGNhbGVuZGFyBShjdGwwMCRNYWluQ29udGVudCRidG5PcmRlckhpc3RvcnlSZWZyZXNoBSljdGwwMCRNYWluQ29udGVudCRidG5PcmRlckhpc3RvcnlEb3dubG9hZAU0Y3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFRpdGxlT3JkZXJDb3VudAU0Y3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFZhbHVlT3JkZXJDb3VudAU1Y3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFRpdGxlUmV0YWlsVG90YWwFK2N0bDAwJE1haW5Db250ZW50JGxibFRvb2x0aXBTdGF0UmV0YWlsVG90YWwFNWN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRWYWx1ZVJldGFpbFRvdGFsBThjdGwwMCRNYWluQ29udGVudCRsYmxPcmRlckhpc3RvcnlTdGF0VGl0bGVXaG9sZXNhbGVUb3RhbAUuY3RsMDAkTWFpbkNvbnRlbnQkbGJsVG9vbHRpcFN0YXRXaG9sZXNhbGVUb3RhbAU4Y3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFZhbHVlV2hvbGVzYWxlVG90YWwFMGN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRUaXRsZVVwbGluZQUrY3RsMDAkTWFpbkNvbnRlbnQkbGJsVG9vbHRpcFN0YXRVcGxpbmVUb3RhbAUwY3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFZhbHVlVXBsaW5lBS1jdGwwMCRNYWluQ29udGVudCRsYmxPcmRlckhpc3RvcnlTdGF0VGl0bGVQU1YFKGN0bDAwJE1haW5Db250ZW50JGxibFRvb2x0aXBTdGF0UFNWVG90YWwFLWN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRWYWx1ZVBTVgUhY3RsMDAkTWFpbkNvbnRlbnQkbHN0T3JkZXJIaXN0b3J5BSVjdGwwMCRNYWluQ29udGVudCRjYm9PcmRlckhpc3RvcnlUeXBlDxQrAAIFCFBlcnNvbmFsBQExZAURY3RsMDAkU2tpbkNob29zZXIPFCsAAmUFB0RlZmF1bHRkvZCeosH5H%2B4TQCYzDgmB1IwM4l%2Fn6veprv0aRO03qrY%3D&__VIEWSTATEGENERATOR=2CBE0447&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=200&__EVENTVALIDATION=%2FwEdAAhzFG8uMqLK05Rf9bd5%2By1t%2FtMFhCET8bj78QUjm1aMzr%2Fm40leH0R5p2hdFFldrQEkbpf2Kczwydbvw%2BedIEgcpHQZAvtR7iyrOhadpU4raJ%2BHHf%2BRU4SxdzfEqCDloQNxu7WHhwuzDBI3rXx%2FsSNyK5Q%2BXyhFw1Q5hmMIpSETz%2Bh81VTPlgN02j8cNlS9u8c%2BSeWC93cDX2wNstzqXI%2BG&ctl00_RadFormDecorator1_ClientState=&ctl00%24MainContent%24cboOrderHistoryType=Customer&ctl00_MainContent_cboOrderHistoryType_ClientState=%7B%22logEntries%22%3A%5B%5D%2C%22value%22%3A%222%22%2C%22text%22%3A%22Customer%22%2C%22enabled%22%3Atrue%2C%22checkedIndices%22%3A%5B%5D%2C%22checkedItemsTextOverflows%22%3Afalse%7D&ctl00%24MainContent%24cboStartDate=2025-08-01&ctl00%24MainContent%24cboStartDate%24dateInput=8%2F1%2F2025&ctl00_MainContent_cboStartDate_calendar_SD=%5B%5B2025%2C8%2C1%5D%5D&ctl00_MainContent_cboStartDate_calendar_AD=%5B%5B1980%2C1%2C1%5D%2C%5B2099%2C12%2C30%5D%2C%5B2025%2C8%2C1%5D%5D&ctl00_MainContent_cboStartDate_dateInput_ClientState=%7B%22enabled%22%3Atrue%2C%22emptyMessage%22%3A%22%22%2C%22validationText%22%3A%222025-08-01-00-00-00%22%2C%22valueAsString%22%3A%222025-08-01-00-00-00%22%2C%22minDateStr%22%3A%221980-01-01-00-00-00%22%2C%22maxDateStr%22%3A%222099-12-31-00-00-00%22%2C%22lastSetTextBoxValue%22%3A%228%2F1%2F2025%22%7D&ctl00_MainContent_cboStartDate_ClientState=&ctl00%24MainContent%24cboEndDate=2025-09-30&ctl00%24MainContent%24cboEndDate%24dateInput=9%2F30%2F2025&ctl00_MainContent_cboEndDate_calendar_SD=%5B%5D&ctl00_MainContent_cboEndDate_calendar_AD=%5B%5B1980%2C1%2C1%5D%2C%5B2099%2C12%2C30%5D%2C%5B2025%2C9%2C1%5D%5D&ctl00_MainContent_cboEndDate_dateInput_ClientState=%7B%22enabled%22%3Atrue%2C%22emptyMessage%22%3A%22%22%2C%22validationText%22%3A%222025-09-30-00-00-00%22%2C%22valueAsString%22%3A%222025-09-30-00-00-00%22%2C%22minDateStr%22%3A%221980-01-01-00-00-00%22%2C%22maxDateStr%22%3A%222099-12-31-00-00-00%22%2C%22lastSetTextBoxValue%22%3A%229%2F30%2F2025%22%7D&ctl00_MainContent_cboEndDate_ClientState=&ctl00%24MainContent%24btnOrderHistoryRefresh=Refresh&ctl00_MainContent_btnOrderHistoryRefresh_ClientState=%7B%22text%22%3A%22Refresh%22%2C%22value%22%3A%22%22%2C%22checked%22%3Afalse%2C%22target%22%3A%22%22%2C%22navigateUrl%22%3A%22%22%2C%22commandName%22%3A%22%22%2C%22commandArgument%22%3A%22%22%2C%22autoPostBack%22%3Atrue%2C%22selectedToggleStateIndex%22%3A0%2C%22validationGroup%22%3Anull%2C%22readOnly%22%3Afalse%2C%22primary%22%3Afalse%2C%22enabled%22%3Atrue%7D&ctl00_MainContent_btnOrderHistoryDownload_ClientState=%7B%22text%22%3A%22Download%22%2C%22value%22%3A%22%22%2C%22checked%22%3Afalse%2C%22target%22%3A%22%22%2C%22navigateUrl%22%3A%22%22%2C%22commandName%22%3A%22%22%2C%22commandArgument%22%3A%22%22%2C%22autoPostBack%22%3Afalse%2C%22selectedToggleStateIndex%22%3A0%2C%22validationGroup%22%3Anull%2C%22readOnly%22%3Afalse%2C%22primary%22%3Afalse%2C%22enabled%22%3Afalse%7D&ctl00_MainContent_lstOrderHistory_ClientState="""  # your long string
    yesterday = get_yesterday_formatted()

    payload = dict(parse_qsl(query))
    payload.update({
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstate_gen,
        "__EVENTVALIDATION": event_validation,
        # Main date inputs (ISO format)
        'ctl00$MainContent$cboStartDate': yesterday['date_iso'],
        'ctl00$MainContent$cboEndDate': yesterday['date_iso'],

        # Date input text boxes (M/D/YYYY format)
        'ctl00$MainContent$cboStartDate$dateInput': yesterday['date_mdY'],
        'ctl00$MainContent$cboEndDate$dateInput': yesterday['date_mdY'],

        # ClientState for date inputs (JSON-like string, but we treat as dict after parsing)
        'ctl00_MainContent_cboStartDate_dateInput_ClientState': f'{{"enabled":true,"emptyMessage":"","validationText":"{yesterday["date_full"]}","valueAsString":"{yesterday["date_full"]}","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"{yesterday["date_mdY"]}"}}',
        'ctl00_MainContent_cboEndDate_dateInput_ClientState': f'{{"enabled":true,"emptyMessage":"","validationText":"{yesterday["date_full"]}","valueAsString":"{yesterday["date_full"]}","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"{yesterday["date_mdY"]}"}}',

        # Selected dates in calendar (as JSON string of list of lists)
        'ctl00_MainContent_cboStartDate_calendar_SD': f'[[{yesterday["date_iso"].split("-")[0]},{int(yesterday["date_iso"].split("-")[1])},{int(yesterday["date_iso"].split("-")[2])}]]',
        'ctl00_MainContent_cboEndDate_calendar_SD': f'[[{yesterday["date_iso"].split("-")[0]},{int(yesterday["date_iso"].split("-")[1])},{int(yesterday["date_iso"].split("-")[2])}]]',

        # Active dates (usually includes min, max, and selected) - preserve range, just update selected
        'ctl00_MainContent_cboStartDate_calendar_AD': f'[[1980,1,1],[2099,12,30],[{yesterday["date_iso"].split("-")[0]},{int(yesterday["date_iso"].split("-")[1])},{int(yesterday["date_iso"].split("-")[2])}]]',
        'ctl00_MainContent_cboEndDate_calendar_AD': f'[[1980,1,1],[2099,12,30],[{yesterday["date_iso"].split("-")[0]},{int(yesterday["date_iso"].split("-")[1])},{int(yesterday["date_iso"].split("-")[2])}]]',

        # Clear any previous ClientState for the dropdowns (optional, but safe)
        'ctl00_MainContent_cboStartDate_ClientState': '',
        'ctl00_MainContent_cboEndDate_ClientState': '',

    })
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://partner.elliemd.com",
        "Referer": ORDER_HISTORY_URL,
        "User-Agent": "Mozilla/5.0",
    }

    r = await session.post(ORDER_HISTORY_URL, data=payload, headers=headers)
    previous_day = []
    if r.status_code != 200:
        return {"status": "Failed to fetch listing"}
    else:
        res = Selector(text=r.text)
        rows = res.xpath("//div[@class='fsOrderHistoryList']//div[contains(@class,'fsOrderRow')]")
        print(f"Total rows found: {len(rows)}")
        for row in rows:
            customer = row.xpath("./*[contains(@class,'fsOrderShipRecipient')]/span[contains(@id,'OrderStatValueShippingRecipient')]/text()").get('')
            if customer:
                print(f"Getting customer: {customer}")
                order_id = row.xpath("./*[contains(@class,'fsOrderNumber ')]//span/@orderid").get('')
                url = f"https://partner.elliemd.com/MemberToolsDotNet/Reports/FirestormOrderReceipt.aspx?OrderID={order_id}"
                r = await session.get(url)
                if r.status_code != 200:
                    return {"status": "Failed to fetch order details", "data": r.text}
                res = Selector(text=r.text)                
                previous_day.append({
                    "status": r.status_code,
                    "order": { 
                        "order_id": order_id,
                        "order_data": res.xpath("//td[text()='Order Date:']/following-sibling::td/text()").get('').strip(),
                        "order_status": res.xpath("//td[text()='Order Status:']/following-sibling::td/text()").get('').strip()
                        },
                    "shipping_address": { 
                        "name":res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[1]").get('').strip(),
                        "street": res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[2]").get('').strip(),
                        "city/state/zip": res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[3]").get('').strip(),
                        "phone": res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[4]").get('').strip(),
                        "email": res.xpath("(//table[@class='SCNODShipToTable']//td[1]/text())[5]").get('').strip()
                        },
                    "products": [ 
                        {
                            'product#': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[1]/text()").get('').strip(),
                            'description': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[2]/text()").get('').strip(),
                            'quantity': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[3]/text()").get('').strip(),
                            'commissionable': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[4]/text()").get('').strip(),
                            'line_total': res.xpath("//tr[@class='SCNODProductTableOddRow']/td[5]/text()").get('').strip()
                        }
                        ],
                    "payment": {
                        'method': res.xpath("//*[contains(text(),'Payment Method')]/text()").get('').replace('Payment Method:', '').strip(), 
                        }
                })
        if previous_day:
            return {"status": "success", "data": previous_day}
        else:
            return {"status": "no_orders", "data": []}
        
@app.get("/")
async def root():
    return {"message": "API is running"}


@app.post("/last")
async def fetch_last(request: Request):
    body = await request.json()
    username = body.get("username")
    password = body.get("password")
    retries = 3
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=200) as session:
                result = await login(
                    username, password, session
                )
                print(f"Login attempt {attempt + 1}: {result}")
                if not result.get("status"):
                    return {"error": "Invalid credentials"}
                if result.get("status"):
                    print("Login successful, fetching listing...")
                    listing = await fetch_last_listing(
                        session
                    )
                    return listing
        except:
            print(f"Attempt {attempt + 1} failed, retrying...")
            if attempt == retries - 1:
                return {"error": "Failed to fetch invoice after multiple attempts"}
            
            

@app.post("/fetch")
async def fetch_invoice(request: Request):
    body = await request.json()
    username = body.get("username")
    password = body.get("password")
    customer_name = body.get("customer_name")
    retries = 3
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=200) as session:
                result = await login(
                    username, password, session
                )
                print(f"Login attempt {attempt + 1}: {result}")
                if not result.get("status"):
                    return {"error": "Invalid credentials"}
                if result.get("status"):
                    print("Login successful, fetching listing...")
                    listing = await fetch_listing(
                        session,
                        customer_name
                    )
                    return listing
        except:
            print(f"Attempt {attempt + 1} failed, retrying...")
            if attempt == retries - 1:
                return {"error": "Failed to fetch invoice after multiple attempts"}
            
            