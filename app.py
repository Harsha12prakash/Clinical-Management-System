import streamlit as st
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import time

# Function to search for the specified product on Flipkart and extract the URL of the product page
def get_product_url(product_name):
    search_url = f"https://www.flipkart.com/search?q={product_name.replace(' ', '+')}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        search_results = soup.find_all('div', {'class': '_75nlfW'})
        if search_results:
            for result in search_results:
                product_link = result.find('a', {'class': 'CGtC98'})
                if product_link:
                    return "https://www.flipkart.com" + product_link['href']
    return None

# Function to scrape product details from the product page URL
def scrape_product_details(product_url):
    if not product_url:
        st.error("Product URL not found.")
        return {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(product_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract product name
        product_name_element = soup.find('span', {'class': 'VU-ZEz'})
        product_name = product_name_element.get_text() if product_name_element else "N/A"

        # If the above approach fails, try finding the product name in other possible locations
        if product_name == "N/A":
            product_name_element = soup.find('h1', {'class': 'yhB1nd'})
            product_name = product_name_element.get_text() if product_name_element else "N/A"

        if product_name == "N/A":
            product_name_element = soup.find('span', {'class': '_35KyD6'})
            product_name = product_name_element.get_text() if product_name_element else "N/A"

        product_price_element = soup.find('div', {'class': 'Nx9bqj CxhGGd'})
        product_price = product_price_element.get_text() if product_price_element else "N/A"

        product_ratings_element = soup.find('div', {'class': 'XQDdHH'})
        product_ratings = product_ratings_element.get_text() if product_ratings_element else "N/A"

        # Find a known element, then navigate to its siblings or children
        # Find the parent div
        parent_div = soup.find('div', {'class': 'col pPAw9M'})

        # Fetch all anchor tags within the parent div
        if parent_div:
            anchor_tags = parent_div.find_all('a')  # Get all links


            # Select the specific link by index (e.g., the first link)
            if len(anchor_tags) > 0:
                review_link_element = anchor_tags[14]  # Change index to select a different link


                if review_link_element and 'href' in review_link_element.attrs:
                    review_link = "https://www.flipkart.com" + review_link_element.attrs['href']


        product_details = {
            'Name': product_name,
            'Price': product_price,
            'Ratings': product_ratings,
            'Review Link' : review_link

        }

        return product_details
    else:
        st.error("Failed to fetch product details.")
        return {}

def fetch_all_reviews(review_link):
    reviews = []
    current_url = review_link

    while current_url:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(current_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            review_elements = soup.find_all('p', {'class': 'z9E0IG'})  # Review texts


            reviews.extend([element.get_text().strip() for element in review_elements])

            # Check for the "Next" link for pagination
            # Check for the "Next" link for pagination
            next_page_element = soup.find('a', {'class': '_9QVEpD'})  # The link to the next page
            if next_page_element and 'href' in next_page_element.attrs:
                # Construct the full URL for the next page
                current_url = "https://www.flipkart.com" + next_page_element['href']
            else:
                # No "Next" link means we've reached the last page
                current_url = None

            # Sleep to avoid rate limiting or being blocked
            time.sleep(1)
        else:
            # Exit loop on HTTP error or if the request fails
            break

    return reviews
    # Function to analyze sentiment of reviews


from transformers import pipeline

# Load the sentiment analysis pipeline
sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")


# Function to analyze sentiment using Hugging Face's sentiment pipeline
def analyze_sentiment(reviews):
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    # Analyze sentiment for each review
    for review in reviews:
        result = sentiment_pipeline(review)[0]  # Get the first result
        sentiment = result["label"]  # This will be 'LABEL_0', 'LABEL_1', or 'LABEL_2'

        # Map sentiment to positive, negative, or neutral
        if sentiment == "LABEL_2":  # Positive sentiment
            positive_count += 1
        elif sentiment == "LABEL_0":  # Negative sentiment
            negative_count += 1
        elif sentiment == "LABEL_1":  # Neutral sentiment
            neutral_count += 1

    total_reviews = len(reviews)
    positive_percentage = (positive_count / total_reviews) * 100
    negative_percentage = (negative_count / total_reviews) * 100
    neutral_percentage = (neutral_count / total_reviews) * 100

    return positive_percentage, negative_percentage, neutral_percentage


def main():
    st.title("Smartphone Review Sentiment Analyzer")

    product_name = st.text_input("Enter the name of the smartphone:")
    if st.button("Analyze Reviews"):
        if product_name:
            st.write(f"Fetching reviews for {product_name}...")
            product_url = get_product_url(product_name)  # You may already have this function
            if product_url:
                product_details = scrape_product_details(product_url)  # Custom scraping logic
                if product_details:
                    st.write("Product Details:")
                    for key, value in product_details.items():
                        st.write(f"{key}: {value}")

                    review_link = product_details.get("Review Link", None)
                    if review_link:
                        reviews = fetch_all_reviews(review_link)
                        if reviews:
                            # Use the new sentiment analysis with pipeline
                            positive_percentage, negative_percentage, neutral_percentage = analyze_sentiment(reviews)
                            st.write(f"Total reviews fetched: {len(reviews)}")
                            st.write(f"Positive reviews: {positive_percentage:.2f}%")
                            st.write(f"Negative reviews: {negative_percentage:.2f}%")
                            st.write(f"Neutral reviews: {neutral_percentage:.2f}%")
                        else:
                            st.write("No reviews found for the specified product.")
                    else:
                        st.error("No review link found.")
                else:
                    st.error("No product details found.")
            else:
                st.error("No product found.")
        else:
            st.error("Please enter the name of the smartphone.")

if __name__ == "__main__":
    main()