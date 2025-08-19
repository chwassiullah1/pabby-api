import asyncio
import httpx
from scrapy import Selector
from fastapi import FastAPI, Request

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
        "txtDealerID": username,
        "Password": password,
        "cboCountry": "USA",
        "btnLogin": "Login"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"
    }

    r = await session.post(LOGIN_URL, data=payload, headers=headers)

    if "Invalid" in r.text or r.status_code != 200:
        return {'status':False}
    return {'status':True, 'viewstate': viewstate, 'event_validation': event_validation, 'viewstate_gen': viewstate_gen}

async def fetch_listing(session: httpx.AsyncClient, viewstate: str, event_validation: str, viewstate_gen: str, customer_name: str):
    url = "https://partner.elliemd.com/MemberToolsDotNet/Reports/FirestormOrderHistoryV4.aspx"
    # payload = {
    #     "Timeout_CountryID": "USA",
    #     "__EVENTTARGET": "",
    #     "__EVENTARGUMENT": "",
    #     "__VIEWSTATE": viewstate,
    #     "__VIEWSTATEGENERATOR": viewstate_gen,
    #     "__EVENTVALIDATION": event_validation,
    #     "ctl00$MainContent$cboOrderHistoryType": "Customer",
    #     "ctl00$MainContent$cboStartDate": "2025-08-01",
    #     "ctl00$MainContent$cboEndDate": "2025-08-31",
    #     "ctl00$MainContent$btnOrderHistoryRefresh": "Refresh",
    # }
    
    payload = 'Timeout_CountryID=USA&ctl00_RadScriptManager1_TSM=%3B%3BSystem.Web.Extensions%2C%20Version%3D4.0.0.0%2C%20Culture%3Dneutral%2C%20PublicKeyToken%3D31bf3856ad364e35%3Aen-US%3A95047a2c-8908-49e3-b68e-d249be89f134%3Aea597d4b%3Ab25378d2%3BTelerik.Web.UI%2C%20Version%3D2024.1.131.45%2C%20Culture%3Dneutral%2C%20PublicKeyToken%3D121fae78165ba3d4%3Aen-US%3A9948a144-ff46-44f4-9ae0-6f54d8eaff7b%3A16e4e7cd%3Aed16cbdc%3A4877f69a%3A33715776%3A86526ba7%3A874f8ea2%3Af7645509%3A24ee1bba%3Af46195d3%3A2003d0b8%3Ac128760b%3A88144a7a%3A1e771326%3Aaa288e2d%3Ab092aa46%3A7c926187%3A8674cba1%3Ab7778d6c%3Ac08e9f8a%3Aa51ee93e%3A59462f1%3A6d43f6d9%3Addbfcb67&__EVENTTARGET=&__EVENTARGUMENT=&__VIEWSTATE=%2FwEPDwUKLTc0NTk4MzUwMQ9kFgJmDw8WBB4PX19BbnRpWHNyZlRva2VuBSBmY2ZmMWJmNWVhOWI0ZTBkYjg2NzVkMjc0OGUxMTc0Zh4SX19BbnRpWHNyZlVzZXJOYW1lZWQWBGYPZBYKAggPFgIeBGhyZWYFH1N0eWxlcy5jc3M%2FdD02Mzg5MTE2Nzk3MTA5ODMzMzRkAgkPFgIfAgUjZnMtYW5pbWF0ZS5jc3M%2FdD02Mzg5MTE2Nzk3MTA5ODMzMzRkAgoPFgIfAgUgZnMtZ3JpZC5jc3M%2FdD02Mzg5MTE2Nzk3MTA5ODMzMzRkAgsPFgIfAgUgZnMtYmFzZS5jc3M%2FdD02Mzg5MTE2Nzk3MTA5ODMzMzRkAgwPFgIfAgUhZnMtdmlkZW8uY3NzP3Q9NjM4OTExNjc5NzEwOTgzMzM0ZAIBDxYCHgVjbGFzcwUqRmlyZXN0b3JtUGFnZV9GaXJlc3Rvcm1PcmRlckhpc3Rvcnl2NF9hc3B4FgICAQ9kFggCAw9kFgJmDxQrAAIPFgQeE2NhY2hlZFNlbGVjdGVkVmFsdWVkHgdWaXNpYmxlaGQQFhVmAgECAgIDAgQCBQIGAgcCCAIJAgoCCwIMAg0CDgIPAhACEQISAhMCFBYVFCsAAg8WBh4EVGV4dAUFQmxhY2seBVZhbHVlBQVCbGFjax4IU2VsZWN0ZWRoZGQUKwACDxYGHwYFD0JsYWNrTWV0cm9Ub3VjaB8HBQ9CbGFja01ldHJvVG91Y2gfCGhkZBQrAAIPFgYfBgUJQm9vdHN0cmFwHwcFCUJvb3RzdHJhcB8IaGRkFCsAAg8WBh8GBQdEZWZhdWx0HwcFB0RlZmF1bHQfCGdkZBQrAAIPFgYfBgUER2xvdx8HBQRHbG93HwhoZGQUKwACDxYGHwYFCE1hdGVyaWFsHwcFCE1hdGVyaWFsHwhoZGQUKwACDxYGHwYFBU1ldHJvHwcFBU1ldHJvHwhoZGQUKwACDxYGHwYFCk1ldHJvVG91Y2gfBwUKTWV0cm9Ub3VjaB8IaGRkFCsAAg8WBh8GBQpPZmZpY2UyMDA3HwcFCk9mZmljZTIwMDcfCGhkZBQrAAIPFgYfBgUPT2ZmaWNlMjAxMEJsYWNrHwcFD09mZmljZTIwMTBCbGFjax8IaGRkFCsAAg8WBh8GBQ5PZmZpY2UyMDEwQmx1ZR8HBQ5PZmZpY2UyMDEwQmx1ZR8IaGRkFCsAAg8WBh8GBRBPZmZpY2UyMDEwU2lsdmVyHwcFEE9mZmljZTIwMTBTaWx2ZXIfCGhkZBQrAAIPFgYfBgUHT3V0bG9vax8HBQdPdXRsb29rHwhoZGQUKwACDxYGHwYFBFNpbGsfBwUEU2lsax8IaGRkFCsAAg8WBh8GBQZTaW1wbGUfBwUGU2ltcGxlHwhoZGQUKwACDxYGHwYFBlN1bnNldB8HBQZTdW5zZXQfCGhkZBQrAAIPFgYfBgUHVGVsZXJpax8HBQdUZWxlcmlrHwhoZGQUKwACDxYGHwYFBVZpc3RhHwcFBVZpc3RhHwhoZGQUKwACDxYGHwYFBVdlYjIwHwcFBVdlYjIwHwhoZGQUKwACDxYGHwYFB1dlYkJsdWUfBwUHV2ViQmx1ZR8IaGRkFCsAAg8WBh8GBQhXaW5kb3dzNx8HBQhXaW5kb3dzNx8IaGRkDxYVZmZmZmZmZmZmZmZmZmZmZmZmZmZmFgEFd1RlbGVyaWsuV2ViLlVJLlJhZENvbWJvQm94SXRlbSwgVGVsZXJpay5XZWIuVUksIFZlcnNpb249MjAyNC4xLjEzMS40NSwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj0xMjFmYWU3ODE2NWJhM2Q0Fi5mDw8WBB4IQ3NzQ2xhc3MFCXJjYkhlYWRlch4EXyFTQgICZGQCAQ8PFgQfCQUJcmNiRm9vdGVyHwoCAmRkAgIPDxYGHwYFBUJsYWNrHwcFBUJsYWNrHwhoZGQCAw8PFgYfBgUPQmxhY2tNZXRyb1RvdWNoHwcFD0JsYWNrTWV0cm9Ub3VjaB8IaGRkAgQPDxYGHwYFCUJvb3RzdHJhcB8HBQlCb290c3RyYXAfCGhkZAIFDw8WBh8GBQdEZWZhdWx0HwcFB0RlZmF1bHQfCGdkZAIGDw8WBh8GBQRHbG93HwcFBEdsb3cfCGhkZAIHDw8WBh8GBQhNYXRlcmlhbB8HBQhNYXRlcmlhbB8IaGRkAggPDxYGHwYFBU1ldHJvHwcFBU1ldHJvHwhoZGQCCQ8PFgYfBgUKTWV0cm9Ub3VjaB8HBQpNZXRyb1RvdWNoHwhoZGQCCg8PFgYfBgUKT2ZmaWNlMjAwNx8HBQpPZmZpY2UyMDA3HwhoZGQCCw8PFgYfBgUPT2ZmaWNlMjAxMEJsYWNrHwcFD09mZmljZTIwMTBCbGFjax8IaGRkAgwPDxYGHwYFDk9mZmljZTIwMTBCbHVlHwcFDk9mZmljZTIwMTBCbHVlHwhoZGQCDQ8PFgYfBgUQT2ZmaWNlMjAxMFNpbHZlch8HBRBPZmZpY2UyMDEwU2lsdmVyHwhoZGQCDg8PFgYfBgUHT3V0bG9vax8HBQdPdXRsb29rHwhoZGQCDw8PFgYfBgUEU2lsax8HBQRTaWxrHwhoZGQCEA8PFgYfBgUGU2ltcGxlHwcFBlNpbXBsZR8IaGRkAhEPDxYGHwYFBlN1bnNldB8HBQZTdW5zZXQfCGhkZAISDw8WBh8GBQdUZWxlcmlrHwcFB1RlbGVyaWsfCGhkZAITDw8WBh8GBQVWaXN0YR8HBQVWaXN0YR8IaGRkAhQPDxYGHwYFBVdlYjIwHwcFBVdlYjIwHwhoZGQCFQ8PFgYfBgUHV2ViQmx1ZR8HBQdXZWJCbHVlHwhoZGQCFg8PFgYfBgUIV2luZG93czcfBwUIV2luZG93czcfCGhkZAIHDw8WCB4VRW5hYmxlRW1iZWRkZWRTY3JpcHRzZx4cRW5hYmxlRW1iZWRkZWRCYXNlU3R5bGVzaGVldGceElJlc29sdmVkUmVuZGVyTW9kZQspclRlbGVyaWsuV2ViLlVJLlJlbmRlck1vZGUsIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMjQuMS4xMzEuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNAEeF0VuYWJsZUFqYXhTa2luUmVuZGVyaW5naBYCHgVzdHlsZQUNZGlzcGxheTpub25lO2QCCQ8PFgIfBgUITGFuZ3VhZ2VkZAIVD2QWCgIBD2QWAmYPZBYEZg9kFgQCAQ8PFgIeCEltYWdlVXJsBRMvZnMtaW1hZ2VzL2xvZ28ucG5nZGQCAw8WAh8PBXxkaXNwbGF5Om5vbmU7IGZvbnQtc2l6ZTogMThweDtjb2xvcjogd2hpdGU7YmFja2dyb3VuZC1jb2xvcjpyZ2IoMTkyLCAxMCwgMTApO2JvcmRlci1yYWRpdXM6IDEwcHggMTBweCAwIDA7cGFkZGluZzogOHB4IDEwcHg7ZAICD2QWBAIBDw8WAh8GBUc8aDEgY2xhc3M9J3dlbGNvbWUnPldlbGNvbWUsIEtlbGxpZSA8c3Bhbj5MZXRzIEdldCBTdGFydGVkITwvc3Bhbj48L2gxPmRkAgIPDxYCHwVoZGQCAw9kFgJmD2QWAgIBDxQrAAIUKwACDxYCHwVoZGRkZAIFDxYCHwVnZAIHDxYCHwVoFgQCAQ8UKwACFCsAAmRkZGQCAw8UKwACFCsAAmRkZGQCCQ9kFgQCAQ8PFgIfBgUNT3JkZXIgSGlzdG9yeWRkAgMPZBYoAgEPFCsAAg8WDh4FTGFiZWwFCk9yZGVyIFR5cGUfBGQfC2cfDGcfDQsrBAIfDmgfBgUIUGVyc29uYWxkEBYCZgIBFgIUKwACDxYGHwYFCFBlcnNvbmFsHwcFATEfCGdkZBQrAAIPFgYfBgUIQ3VzdG9tZXIfBwUBMh8IaGRkDxYCZmYWAQV3VGVsZXJpay5XZWIuVUkuUmFkQ29tYm9Cb3hJdGVtLCBUZWxlcmlrLldlYi5VSSwgVmVyc2lvbj0yMDI0LjEuMTMxLjQ1LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPTEyMWZhZTc4MTY1YmEzZDQWCGYPDxYEHwkFCXJjYkhlYWRlch8KAgJkZAIBDw8WBB8JBQlyY2JGb290ZXIfCgICZGQCAg8PFgYfBgUIUGVyc29uYWwfBwUBMR8IZ2RkAgMPDxYGHwYFCEN1c3RvbWVyHwcFATIfCGhkZAIDDw8WCh4MU2VsZWN0ZWREYXRlBgBAxFuO0N0IHhFfc2tpcE1NVmFsaWRhdGlvbmgfC2cfDGcfDQsrBAJkFgRmDxQrAAgPFhQfEQUKU3RhcnQgRGF0ZR8GBRMyMDI1LTA4LTAxLTAwLTAwLTAwHhFFbmFibGVBcmlhU3VwcG9ydGgeDUxhYmVsQ3NzQ2xhc3MFB3JpTGFiZWwfDmgeBFNraW4FBVZpc3RhHwxnHxNoHw0LKwQCHwtnZBYGHgpSZXNpemVNb2RlCylyVGVsZXJpay5XZWIuVUkuUmVzaXplTW9kZSwgVGVsZXJpay5XZWIuVUksIFZlcnNpb249MjAyNC4xLjEzMS40NSwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj0xMjFmYWU3ODE2NWJhM2Q0AB8JBRFyaVRleHRCb3ggcmlIb3Zlch8KAgIWBh8XCysFAB8JBRFyaVRleHRCb3ggcmlFcnJvch8KAgIWBh8XCysFAB8JBRNyaVRleHRCb3ggcmlGb2N1c2VkHwoCAhYEHwkFE3JpVGV4dEJveCByaUVuYWJsZWQfCgICFgYfFwsrBQAfCQUUcmlUZXh0Qm94IHJpRGlzYWJsZWQfCgICFgYfFwsrBQAfCQURcmlUZXh0Qm94IHJpRW1wdHkfCgICFgYfFwsrBQAfCQUQcmlUZXh0Qm94IHJpUmVhZB8KAgJkAgIPFCsADQ8WCAUNU2VsZWN0ZWREYXRlcw8FjwFUZWxlcmlrLldlYi5VSS5DYWxlbmRhci5Db2xsZWN0aW9ucy5EYXRlVGltZUNvbGxlY3Rpb24sIFRlbGVyaWsuV2ViLlVJLCBWZXJzaW9uPTIwMjQuMS4xMzEuNDUsIEN1bHR1cmU9bmV1dHJhbCwgUHVibGljS2V5VG9rZW49MTIxZmFlNzgxNjViYTNkNBQrAAAFC1NwZWNpYWxEYXlzDwWSAVRlbGVyaWsuV2ViLlVJLkNhbGVuZGFyLkNvbGxlY3Rpb25zLkNhbGVuZGFyRGF5Q29sbGVjdGlvbiwgVGVsZXJpay5XZWIuVUksIFZlcnNpb249MjAyNC4xLjEzMS40NSwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj0xMjFmYWU3ODE2NWJhM2Q0FCsAAAUPUmVuZGVySW52aXNpYmxlZwURRW5hYmxlTXVsdGlTZWxlY3RoDxYMHwtnHwxnHxRoHxYFBVZpc3RhHw0LKwQCHw5oZGQWBB8JBQtyY01haW5UYWJsZR8KAgIWBB8JBQxyY090aGVyTW9udGgfCgICZBYEHwkFCnJjU2VsZWN0ZWQfCgICZBYEHwkFCnJjRGlzYWJsZWQfCgICFgQfCQUMcmNPdXRPZlJhbmdlHwoCAhYEHwkFCXJjV2Vla2VuZB8KAgIWBB8JBQdyY0hvdmVyHwoCAhYEHwkFL1JhZENhbGVuZGFyTW9udGhWaWV3IFJhZENhbGVuZGFyTW9udGhWaWV3X1Zpc3RhHwoCAhYEHwkFCXJjVmlld1NlbB8KAgJkAgUPDxYKHxIGAMAoVCHo3QgfE2gfC2cfDGcfDQsrBAJkFgRmDxQrAAgPFhQfEQUIRW5kIERhdGUfBgUTMjAyNS0wOC0zMS0wMC0wMC0wMB8UaB8VBQdyaUxhYmVsHw5oHxYFBVZpc3RhHwxnHxNoHw0LKwQCHwtnZBYGHxcLKwUAHwkFEXJpVGV4dEJveCByaUhvdmVyHwoCAhYGHxcLKwUAHwkFEXJpVGV4dEJveCByaUVycm9yHwoCAhYGHxcLKwUAHwkFE3JpVGV4dEJveCByaUZvY3VzZWQfCgICFgQfCQUTcmlUZXh0Qm94IHJpRW5hYmxlZB8KAgIWBh8XCysFAB8JBRRyaVRleHRCb3ggcmlEaXNhYmxlZB8KAgIWBh8XCysFAB8JBRFyaVRleHRCb3ggcmlFbXB0eR8KAgIWBh8XCysFAB8JBRByaVRleHRCb3ggcmlSZWFkHwoCAmQCAg8UKwANDxYIBQ1TZWxlY3RlZERhdGVzDwWPAVRlbGVyaWsuV2ViLlVJLkNhbGVuZGFyLkNvbGxlY3Rpb25zLkRhdGVUaW1lQ29sbGVjdGlvbiwgVGVsZXJpay5XZWIuVUksIFZlcnNpb249MjAyNC4xLjEzMS40NSwgQ3VsdHVyZT1uZXV0cmFsLCBQdWJsaWNLZXlUb2tlbj0xMjFmYWU3ODE2NWJhM2Q0FCsAAAULU3BlY2lhbERheXMPBZIBVGVsZXJpay5XZWIuVUkuQ2FsZW5kYXIuQ29sbGVjdGlvbnMuQ2FsZW5kYXJEYXlDb2xsZWN0aW9uLCBUZWxlcmlrLldlYi5VSSwgVmVyc2lvbj0yMDI0LjEuMTMxLjQ1LCBDdWx0dXJlPW5ldXRyYWwsIFB1YmxpY0tleVRva2VuPTEyMWZhZTc4MTY1YmEzZDQUKwAABQ9SZW5kZXJJbnZpc2libGVnBRFFbmFibGVNdWx0aVNlbGVjdGgPFgwfC2cfDGcfFGgfFgUFVmlzdGEfDQsrBAIfDmhkZBYEHwkFC3JjTWFpblRhYmxlHwoCAhYEHwkFDHJjT3RoZXJNb250aB8KAgJkFgQfCQUKcmNTZWxlY3RlZB8KAgJkFgQfCQUKcmNEaXNhYmxlZB8KAgIWBB8JBQxyY091dE9mUmFuZ2UfCgICFgQfCQUJcmNXZWVrZW5kHwoCAhYEHwkFB3JjSG92ZXIfCgICFgQfCQUvUmFkQ2FsZW5kYXJNb250aFZpZXcgUmFkQ2FsZW5kYXJNb250aFZpZXdfVmlzdGEfCgICFgQfCQUJcmNWaWV3U2VsHwoCAmQCBw88KwAFAQAPFgofBgUHUmVmcmVzaB8OaB8MZx8NCysEAh8LZ2RkAgkPPCsABQEADxYMHgdFbmFibGVkaB8GBQhEb3dubG9hZB8OaB8MZx8NCysEAh8LZ2RkAgsPDxYKHwYFDFRvdGFsIE9yZGVycx8LZx8MZx8NCysEAR8OaGRkAg0PDxYKHwYFATAfC2cfDGcfDQsrBAEfDmhkZAIPDw8WCh8GBR9SZXRhaWwgVG90YWwgKEN1c3RvbWVyIFByaWNpbmcpHwtnHwxnHw0LKwQBHw5oZGQCEQ8PFgofBgVmVGhpcyBhbW91bnQgZG9lcyBub3QgaW5jbHVkZSBhbnkgdm9sdW1lIGZyb20gb3JkZXJzIG9yIG9yZGVyIGRldGFpbHMgdGhhdCBoYXZlIGJlZW4gdm9pZGVkIG9yIG9uIGhvbGQuHwtnHwxnHw0LKwQBHw5oZGQCEw8PFgofBgUFJDAuMDAfC2cfDGcfDQsrBAEfDmhkZAIVDw8WCh8GBSRSZXRhaWwgVG90YWwgKEJyYW5kIFBhcnRuZXIgUHJpY2luZykfC2cfDGcfDQsrBAEfDmhkZAIXDw8WCh8GBWZUaGlzIGFtb3VudCBkb2VzIG5vdCBpbmNsdWRlIGFueSB2b2x1bWUgZnJvbSBvcmRlcnMgb3Igb3JkZXIgZGV0YWlscyB0aGF0IGhhdmUgYmVlbiB2b2lkZWQgb3Igb24gaG9sZC4fC2cfDGcfDQsrBAEfDmhkZAIZDw8WCh8GBQUkMC4wMB8LZx8MZx8NCysEAR8OaGRkAhsPDxYKHwYFGENvbW1pc3Npb25hbCBWb2x1bWUgKENWKR8LZx8MZx8NCysEAR8OaGRkAh0PDxYKHwYFZlRoaXMgYW1vdW50IGRvZXMgbm90IGluY2x1ZGUgYW55IHZvbHVtZSBmcm9tIG9yZGVycyBvciBvcmRlciBkZXRhaWxzIHRoYXQgaGF2ZSBiZWVuIHZvaWRlZCBvciBvbiBob2xkLh8LZx8MZx8NCysEAR8OaGRkAh8PDxYKHwYFBSQwLjAwHwtnHwxnHw0LKwQBHw5oZGQCIQ8PFgofBgUJUFNWIFRvdGFsHwtnHwxnHw0LKwQBHw5oZGQCIw8PFgofBgVmVGhpcyBhbW91bnQgZG9lcyBub3QgaW5jbHVkZSBhbnkgdm9sdW1lIGZyb20gb3JkZXJzIG9yIG9yZGVyIGRldGFpbHMgdGhhdCBoYXZlIGJlZW4gdm9pZGVkIG9yIG9uIGhvbGQuHwtnHwxnHw0LKwQBHw5oZGQCJQ8PFgofBgUFJDAuMDAfC2cfDGcfDQsrBAEfDmhkZAInDxQrAAYPFgweC18hRGF0YUJvdW5kZx8LZx8OaB8MZx4LXyFJdGVtQ291bnRmHw0LKwQCZBQrAANkZBQrAAIWAh4RSXRlbVBsYWNlSG9sZGVySUQFN2N0bDAwX01haW5Db250ZW50X2xzdE9yZGVySGlzdG9yeV9PcmRlckhpc3RvcnlDb250YWluZXJkFCsAAw8FBl8hRFNJQ2YPBQtfIUl0ZW1Db3VudGYPBQhfIVBDb3VudGRkFgIeAl9jZmRkGAMFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYZBRdjdGwwMCRSYWRGb3JtRGVjb3JhdG9yMQUlY3RsMDAkTWFpbkNvbnRlbnQkY2JvT3JkZXJIaXN0b3J5VHlwZQUeY3RsMDAkTWFpbkNvbnRlbnQkY2JvU3RhcnREYXRlBSdjdGwwMCRNYWluQ29udGVudCRjYm9TdGFydERhdGUkY2FsZW5kYXIFJ2N0bDAwJE1haW5Db250ZW50JGNib1N0YXJ0RGF0ZSRjYWxlbmRhcgUcY3RsMDAkTWFpbkNvbnRlbnQkY2JvRW5kRGF0ZQUlY3RsMDAkTWFpbkNvbnRlbnQkY2JvRW5kRGF0ZSRjYWxlbmRhcgUlY3RsMDAkTWFpbkNvbnRlbnQkY2JvRW5kRGF0ZSRjYWxlbmRhcgUoY3RsMDAkTWFpbkNvbnRlbnQkYnRuT3JkZXJIaXN0b3J5UmVmcmVzaAUpY3RsMDAkTWFpbkNvbnRlbnQkYnRuT3JkZXJIaXN0b3J5RG93bmxvYWQFNGN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRUaXRsZU9yZGVyQ291bnQFNGN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRWYWx1ZU9yZGVyQ291bnQFNWN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRUaXRsZVJldGFpbFRvdGFsBStjdGwwMCRNYWluQ29udGVudCRsYmxUb29sdGlwU3RhdFJldGFpbFRvdGFsBTVjdGwwMCRNYWluQ29udGVudCRsYmxPcmRlckhpc3RvcnlTdGF0VmFsdWVSZXRhaWxUb3RhbAU4Y3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFRpdGxlV2hvbGVzYWxlVG90YWwFLmN0bDAwJE1haW5Db250ZW50JGxibFRvb2x0aXBTdGF0V2hvbGVzYWxlVG90YWwFOGN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRWYWx1ZVdob2xlc2FsZVRvdGFsBTBjdGwwMCRNYWluQ29udGVudCRsYmxPcmRlckhpc3RvcnlTdGF0VGl0bGVVcGxpbmUFK2N0bDAwJE1haW5Db250ZW50JGxibFRvb2x0aXBTdGF0VXBsaW5lVG90YWwFMGN0bDAwJE1haW5Db250ZW50JGxibE9yZGVySGlzdG9yeVN0YXRWYWx1ZVVwbGluZQUtY3RsMDAkTWFpbkNvbnRlbnQkbGJsT3JkZXJIaXN0b3J5U3RhdFRpdGxlUFNWBShjdGwwMCRNYWluQ29udGVudCRsYmxUb29sdGlwU3RhdFBTVlRvdGFsBS1jdGwwMCRNYWluQ29udGVudCRsYmxPcmRlckhpc3RvcnlTdGF0VmFsdWVQU1YFIWN0bDAwJE1haW5Db250ZW50JGxzdE9yZGVySGlzdG9yeQUlY3RsMDAkTWFpbkNvbnRlbnQkY2JvT3JkZXJIaXN0b3J5VHlwZQ8UKwACBQhQZXJzb25hbAUBMWQFEWN0bDAwJFNraW5DaG9vc2VyDxQrAAJlBQdEZWZhdWx0ZKKJwtRDXBwAyBAGrC45wHa4MTUcQn6zo9ndTnxKgTy5&__VIEWSTATEGENERATOR=2CBE0447&__SCROLLPOSITIONX=0&__SCROLLPOSITIONY=320.79998779296875&__EVENTVALIDATION=%2FwEdAAgBA7bVIQQZ2hkVIA8s8xcO%2FtMFhCET8bj78QUjm1aMzr%2Fm40leH0R5p2hdFFldrQEkbpf2Kczwydbvw%2BedIEgcpHQZAvtR7iyrOhadpU4raJ%2BHHf%2BRU4SxdzfEqCDloQNxu7WHhwuzDBI3rXx%2FsSNyK5Q%2BXyhFw1Q5hmMIpSETz3QVqs23XB%2FjDT2Kp2LJkXiJI0lOm573qOR13Sjotx6h&ctl00_RadFormDecorator1_ClientState=&ctl00%24MainContent%24cboOrderHistoryType=Customer&ctl00_MainContent_cboOrderHistoryType_ClientState=%7B%22logEntries%22%3A%5B%5D%2C%22value%22%3A%222%22%2C%22text%22%3A%22Customer%22%2C%22enabled%22%3Atrue%2C%22checkedIndices%22%3A%5B%5D%2C%22checkedItemsTextOverflows%22%3Afalse%7D&ctl00%24MainContent%24cboStartDate=2025-08-01&ctl00%24MainContent%24cboStartDate%24dateInput=8%2F1%2F2025&ctl00_MainContent_cboStartDate_calendar_SD=%5B%5D&ctl00_MainContent_cboStartDate_calendar_AD=%5B%5B1980%2C1%2C1%5D%2C%5B2099%2C12%2C30%5D%2C%5B2025%2C8%2C19%5D%5D&ctl00_MainContent_cboStartDate_dateInput_ClientState=%7B%22enabled%22%3Atrue%2C%22emptyMessage%22%3A%22%22%2C%22validationText%22%3A%222025-08-01-00-00-00%22%2C%22valueAsString%22%3A%222025-08-01-00-00-00%22%2C%22minDateStr%22%3A%221980-01-01-00-00-00%22%2C%22maxDateStr%22%3A%222099-12-31-00-00-00%22%2C%22lastSetTextBoxValue%22%3A%228%2F1%2F2025%22%7D&ctl00_MainContent_cboStartDate_ClientState=&ctl00%24MainContent%24cboEndDate=2025-08-31&ctl00%24MainContent%24cboEndDate%24dateInput=8%2F31%2F2025&ctl00_MainContent_cboEndDate_calendar_SD=%5B%5D&ctl00_MainContent_cboEndDate_calendar_AD=%5B%5B1980%2C1%2C1%5D%2C%5B2099%2C12%2C30%5D%2C%5B2025%2C8%2C19%5D%5D&ctl00_MainContent_cboEndDate_dateInput_ClientState=%7B%22enabled%22%3Atrue%2C%22emptyMessage%22%3A%22%22%2C%22validationText%22%3A%222025-08-31-00-00-00%22%2C%22valueAsString%22%3A%222025-08-31-00-00-00%22%2C%22minDateStr%22%3A%221980-01-01-00-00-00%22%2C%22maxDateStr%22%3A%222099-12-31-00-00-00%22%2C%22lastSetTextBoxValue%22%3A%228%2F31%2F2025%22%7D&ctl00_MainContent_cboEndDate_ClientState=&ctl00%24MainContent%24btnOrderHistoryRefresh=Refresh&ctl00_MainContent_btnOrderHistoryRefresh_ClientState=%7B%22text%22%3A%22Refresh%22%2C%22value%22%3A%22%22%2C%22checked%22%3Afalse%2C%22target%22%3A%22%22%2C%22navigateUrl%22%3A%22%22%2C%22commandName%22%3A%22%22%2C%22commandArgument%22%3A%22%22%2C%22autoPostBack%22%3Atrue%2C%22selectedToggleStateIndex%22%3A0%2C%22validationGroup%22%3Anull%2C%22readOnly%22%3Afalse%2C%22primary%22%3Afalse%2C%22enabled%22%3Atrue%7D&ctl00_MainContent_btnOrderHistoryDownload_ClientState=%7B%22text%22%3A%22Download%22%2C%22value%22%3A%22%22%2C%22checked%22%3Afalse%2C%22target%22%3A%22%22%2C%22navigateUrl%22%3A%22%22%2C%22commandName%22%3A%22%22%2C%22commandArgument%22%3A%22%22%2C%22autoPostBack%22%3Afalse%2C%22selectedToggleStateIndex%22%3A0%2C%22validationGroup%22%3Anull%2C%22readOnly%22%3Afalse%2C%22primary%22%3Afalse%2C%22enabled%22%3Afalse%7D&ctl00_MainContent_lstOrderHistory_ClientState='
    headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://partner.elliemd.com',
    'priority': 'u=0, i',
    'referer': 'https://partner.elliemd.com/MemberToolsDotNet/Reports/FirestormOrderHistoryV4.aspx',
    'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'Cookie': 'ASP.NET_SessionId=av1l3bu3aw3iq0dawit3ky4m; SESSIONDealerID=821859; 821859_av1l3bu3aw3iq0dawit3ky4m_DealerID=821859; 821859_av1l3bu3aw3iq0dawit3ky4m_CountryID=USA; FirestormLanguageID=2; __AntiXsrfToken=fcff1bf5ea9b4e0db8675d2748e1174f; Timeout_CountryID=USA; Timeout_CountryID=USA'
    }
    r = await session.post(url, data=payload, headers=headers, timeout=200)
    if r.status_code != 200:
        return {"status": "Failed to fetch listing"}
    else:
        res = Selector(text=r.text)
        rows = res.xpath("//div[@class='fsOrderHistoryList']//div[contains(@class,'fsOrderRow')]")
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
@app.get("/")
async def root():
    return {"message": "API is running"}

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
                result = await login(username, password, session)
                if not result.get("status"):
                    return {"error": "Invalid credentials"}
                if result.get("status"):
                    print("Login successful, fetching listing...")
                    listing = await fetch_listing(
                        session,
                        result.get("viewstate"),
                        result.get("event_validation"),
                        result.get("viewstate_gen"),
                        customer_name
                    )
                    return listing
        except:
            print(f"Attempt {attempt + 1} failed, retrying...")
            if attempt == retries - 1:
                return {"error": "Failed to fetch invoice after multiple attempts"}
            
            