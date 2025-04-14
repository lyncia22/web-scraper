import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime


logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


BASE_URL = "https://vacancymail.co.zw/jobs"
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def scrape_jobs():
    try:
        logging.info("Starting job scrape...")
        print("🔍 Scraping jobs...")

        response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        job_cards = soup.select('a.job-listing')  

        if not job_cards:
            with open("page_debug.html", "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            print("⚠️ No job cards found. Dumped HTML to page_debug.html for inspection.")
            return

        print(f"✅ Found {len(job_cards)} job listings.")
        job_list = []

        for job in job_cards:
            try:
                
                title = job.select_one('h3.job-listing-title')
                company = job.select_one('h4.job-listing-company')
                description = job.select_one('p.job-listing-text')

                
                title = title.get_text(strip=True) if title else "No Title"
                company = company.get_text(strip=True) if company else "No Company"
                description = description.get_text(strip=True) if description else "No Description"

                
                footer_items = job.select('div.job-listing-footer li')
                location = expiry = "Unknown"

                for item in footer_items:
                    text = item.get_text(strip=True)
                    if "Expires" in text:
                        expiry = text.replace("Expires", "").strip()
                    elif not location or location == "Unknown":
                        location = text  

                job_list.append({
                    "Job Title": title,
                    "Company": company,
                    "Location": location,
                    "Expiry Date": expiry,
                    "Description": description,
                    "Link": f"https://vacancymail.co.zw{job['href']}"  
                })

            except Exception as e:
                logging.warning(f"Could not parse one job: {e}")
                print(f"⚠️ Skipped one job due to error: {e}")

        if not job_list:
            logging.error("No jobs scraped after parsing loop.")
            print("❌ No jobs scraped. Something went wrong.")
            return

      
        df = pd.DataFrame(job_list)
        df.drop_duplicates(subset=["Job Title", "Company", "Location"], inplace=True)
        df["Expiry Date"] = pd.to_datetime(df["Expiry Date"], errors='coerce').dt.strftime('%Y-%m-%d')

        df.to_csv("scraped_data.csv", index=False)
        logging.info("Job scrape successful. Data saved to scraped_data.csv.")
        print("✅ scraped_data.csv created with", len(df), "jobs.")

    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        print("❌ Something went wrong. Check scraper.log for details.")


if __name__ == "__main__":
    print("🚀 Running web scraper now...\n")
    scrape_jobs()
