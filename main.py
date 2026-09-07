
import asyncio
import re
import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pdfplumber
from playwright.async_api import async_playwright


URL = (
    "https://wrd.maharashtra.gov.in/Site/ViewPDFList?"
    "doctype=BTOLaLNhA0/q1GTf08fcNQN43JuJzENBtWSJwpAPMdgCPB0nLNI/"
    "L7AcnDUxfgYUyBtUXiLMcs6zX9kgTMjLefMEy4jeFOsSz4OAJEBdDWI="
)

OUTPUT_DIR = Path("khadakwasla_data")
PDF_DIR = OUTPUT_DIR / "pdfs"

OUTPUT_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------
# 1. Extract Khadakwasla information from PDF
# ---------------------------------------------------------

def extract_khadakwasla(pdf_path):
    """
    Searches every page for Khadakwasla/खडकवासला.
    Returns the matching text/table rows.
    """

    results = []

    try:
        with pdfplumber.open(pdf_path) as pdf:

            for page_number, page in enumerate(pdf.pages, start=1):

                # Try tables first
                tables = page.extract_tables()

                for table in tables:

                    for row in table:

                        if not row:
                            continue

                        row_text = " | ".join(
                            str(cell).strip() if cell else ""
                            for cell in row
                        )

                        if (
                            "Khadakwasla" in row_text
                            or "KHADAKWASLA" in row_text.upper()
                            or "खडकवासला" in row_text
                        ):
                            results.append({
                                "page": page_number,
                                "type": "table",
                                "data": row_text
                            })

                # Also search normal text
                text = page.extract_text() or ""

                for line in text.splitlines():

                    if (
                        "Khadakwasla" in line
                        or "KHADAKWASLA" in line.upper()
                        or "खडकवासला" in line
                    ):
                        results.append({
                            "page": page_number,
                            "type": "text",
                            "data": line.strip()
                        })

    except Exception as e:
        print(f"PDF extraction error: {pdf_path}: {e}")

    return results


# ---------------------------------------------------------
# 2. Open WRD website and download reports
# ---------------------------------------------------------

async def scrape():

    async with async_playwright() as p:

        browser = await p.chromium.launch(
    executable_path="/usr/bin/brave-origin",
    headless=False
)
        

        page = await browser.new_page(
            accept_downloads=True
        )

        print("Opening WRD website...")
        await page.goto(
            URL,
            wait_until="networkidle",
            timeout=120000
        )

        print("Website loaded.")

        # -------------------------------------------------
        # Find date inputs
        # -------------------------------------------------

        inputs = await page.locator("input").all()

        print(f"Found {len(inputs)} input fields.")

        for i, element in enumerate(inputs):

            try:
                print(
                    i,
                    await element.get_attribute("name"),
                    await element.get_attribute("id"),
                    await element.get_attribute("type")
                )
            except:
                pass

        # -------------------------------------------------
        # DATE RANGE
        # -------------------------------------------------

        end_date = date.today()
        start_date = end_date - timedelta(days=365)

        start_string = start_date.strftime("%d/%m/%Y")
        end_string = end_date.strftime("%d/%m/%Y")

        print()
        print("Collecting:")
        print(start_string, "to", end_string)
        print()

        # -------------------------------------------------
        # Try to identify date inputs
        # -------------------------------------------------

        date_inputs = page.locator(
            'input[type="date"], '
            'input[placeholder*="date" i], '
            'input[name*="date" i], '
            'input[id*="date" i]'
        )

        count = await date_inputs.count()

        print("Possible date inputs:", count)

        # -------------------------------------------------
        # Fill dates
        # -------------------------------------------------

        if count >= 2:

            await date_inputs.nth(0).fill(
                start_date.strftime("%Y-%m-%d")
            )

            await date_inputs.nth(1).fill(
                end_date.strftime("%Y-%m-%d")
            )

        else:

            print(
                "\nCould not automatically identify date fields."
            )

            print(
                "The browser is open so you can inspect the page."
            )

            await page.pause()

        # -------------------------------------------------
        # Search
        # -------------------------------------------------

        buttons = page.locator("button")

        button_count = await buttons.count()

        print("Buttons:", button_count)

        for i in range(button_count):

            try:

                text = (
                    await buttons.nth(i).inner_text()
                ).strip()

                print("BUTTON:", i, repr(text))

            except:
                pass

        # Try common search buttons
        search_buttons = page.get_by_text(
            re.compile(
                "शोधा|Search|search|submit",
                re.IGNORECASE
            )
        )

        if await search_buttons.count():

            await search_buttons.first.click()

        else:

            print(
                "Search button not automatically detected."
            )

            await page.pause()

        await page.wait_for_load_state(
            "networkidle"
        )

        # -------------------------------------------------
        # Collect report links
        # -------------------------------------------------

        links = page.locator("a")

        link_count = await links.count()

        print(
            f"\nFound {link_count} links."
        )

        report_links = []

        for i in range(link_count):

            link = links.nth(i)

            try:

                href = await link.get_attribute("href")

                text = (
                    await link.inner_text()
                ).strip()

                if not href:
                    continue

                # Look for PDF/report links
                if (
                    ".pdf" in href.lower()
                    or "pdf" in text.lower()
                    or "बघा" in text
                ):

                    report_links.append(
                        (text, href)
                    )

            except:
                pass

        print(
            f"Potential reports found: {len(report_links)}"
        )

        # -------------------------------------------------
        # Download reports
        # -------------------------------------------------

        extracted_rows = []

        for index, (text, href) in enumerate(
            report_links,
            start=1
        ):

            print(
                f"\n[{index}/{len(report_links)}]"
            )

            print(text)
            print(href)

            try:

                # Open report
                report_page = await browser.new_page()

                await report_page.goto(
                    href,
                    wait_until="networkidle",
                    timeout=120000
                )

                # If browser displays PDF,
                # save the response manually where possible.

                pdf_url = report_page.url

                if ".pdf" not in pdf_url.lower():

                    await report_page.close()
                    continue

                response = await page.request.get(
                    pdf_url
                )

                pdf_bytes = await response.body()

                filename = (
                    f"report_{index:04d}.pdf"
                )

                pdf_path = PDF_DIR / filename

                pdf_path.write_bytes(
                    pdf_bytes
                )

                await report_page.close()

                print(
                    "Saved:",
                    pdf_path
                )

                # Extract Khadakwasla
                matches = extract_khadakwasla(
                    pdf_path
                )

                if matches:

                    for match in matches:

                        extracted_rows.append({
                            "report_number": index,
                            "source_pdf": filename,
                            "page": match["page"],
                            "type": match["type"],
                            "raw_data": match["data"]
                        })

                        print(
                            "  ✓ KHADAKWASLA FOUND:",
                            match["data"]
                        )

                else:

                    print(
                        "  Khadakwasla not found."
                    )

            except Exception as e:

                print(
                    "ERROR:",
                    e
                )

        # -------------------------------------------------
        # Save raw extracted data
        # -------------------------------------------------

        if extracted_rows:

            df = pd.DataFrame(
                extracted_rows
            )

            csv_path = (
                OUTPUT_DIR /
                "khadakwasla_raw.csv"
            )

            excel_path = (
                OUTPUT_DIR /
                "khadakwasla_raw.xlsx"
            )

            df.to_csv(
                csv_path,
                index=False,
                encoding="utf-8-sig"
            )

            df.to_excel(
                excel_path,
                index=False
            )

            print(
                "\n================================"
            )

            print(
                "DATA COLLECTION COMPLETE"
            )

            print(
                "CSV:",
                csv_path
            )

            print(
                "Excel:",
                excel_path
            )

            print(
                "Rows:",
                len(df)
            )

            print(
                "================================"
            )

        else:

            print(
                "\nNo Khadakwasla data extracted."
            )

        await browser.close()


# ---------------------------------------------------------
# Run
# ---------------------------------------------------------

if __name__ == "__main__":

    asyncio.run(scrape())