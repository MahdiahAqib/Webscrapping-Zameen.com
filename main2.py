# Step 1: Data Collection: Create a web scraper to extract property listings and details from the target real estate
# website.
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd

# Function to scrape property data for a city
def scrape_property_data(driver, city_name):
    try:
        results = []

        # Scrape data from the first four pages of the city
        for page in range(1, 5):
            # since the url is in the form https://www.zameen.com/Homes/Lahore-1-1.html and the next page would be
            # https://www.zameen.com/Homes/Lahore-1-2.html we split it and use the value of counter
            url = urlList[counter].split('.html')[0][:-1] + f'{page}.html'
            print(url)
            driver.get(url)
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # Check if property is available/exists
            if soup.find('span', class_='_5264eceb') is not None and \
                    soup.find('span', class_='_5264eceb').text.strip() == 'No property found':
                break

            # Scrape property's title, prices, location and details
            titles = [title.text.strip() for title in soup.select('h2.c0df3811')]
            prices = [price.text.strip() for price in soup.select('span[aria-label="Price"]')]
            locations = [location.text.strip() for location in soup.select('div._162e6469')]
            details = [detail.text.strip() for detail in soup.select('span.b779b320')]

            # ensure that list for each attribute are of the same length
            smallest = min([len(titles), len(locations), len(prices), len(details)])

            for i in range(smallest):
                results.append([titles[i], locations[i], prices[i], details[i], city_name])

        # Print the data for this city
        print(f"Property data scraped for {city_name}: {len(results)} properties")
        for result in results:
            print(result)

        # Save the data to a CSV file
        if results:
            columns = ['Title', 'Location', 'Price', 'Details', 'City']
            df = pd.DataFrame(results, columns=columns)

            # Append to existing CSV or create a new one
            with open(csv_file, 'a', newline='') as f:
                df.to_csv(f, index=False, header=f.tell() == 0)
            print(f"Property data for {city_name} saved to {csv_file}")

    except Exception as e:
        print(f"Error scraping property data for {city_name}: {str(e)}")


# Set Chrome options
chrome_options = Options()

# Initialize the Chrome WebDriver
driver = webdriver.Chrome(options=chrome_options)

counter, urlList = 0, []
clicked_cities = []  # New list to keep track of clicked cities
num_cities_to_collect = 5
csv_file = "zameenScrappedData.csv"

while len(urlList) < num_cities_to_collect:
    try:
        driver.get("https://www.zameen.com/")

        # Wait for city dropdown button to be clickable & then click it
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="body-wrapper"]/header/div[6]/div/div[2]/div[2]/div[1]/div[1]/div/div'))).click()

        # find drop down menu that contains city names
        dropdown = driver.find_element(By.CLASS_NAME, 'ede17658')

        # find all button elements inside this drop down menu
        buttons = dropdown.find_elements(By.TAG_NAME, 'button')

        # Check if the city has not been clicked already
        city_name = buttons[counter].text
        if city_name not in clicked_cities:
            buttons[counter].click()
            # City has been selected, now click find button
            driver.find_element(By.XPATH, '//*[@id="body-wrapper"]/header/div[6]/div/div[2]/div[2]/div[1]/a').click()
            # successfully at the cities page, now save the url
            urlList.append(driver.current_url)
            # Print a message indicating the progress
            print(f"Collected URL for City: {city_name}")
            # Add the city to the list of clicked cities
            clicked_cities.append(city_name)

            # Scrape property data for this city
            print(f"Scraping property data for {city_name}...")
            scrape_property_data(driver, city_name)

        # Increment the counter for the next city
        counter += 1
        # Will break once the desired amount of city urls has been collected
        if len(urlList) >= num_cities_to_collect:
            break
    except Exception as e:
        continue

# Close the webdriver after processing all the buttons
driver.quit()

# Step 2: Data Cleaning: Clean and preprocess the scraped data, handle missing values, and ensure data consistency.
import pandas as pd
data = pd.read_csv('zameenScrappedData.csv')
print(data.head(10))
data.dropna(inplace=True)
data.drop_duplicates(inplace=True)
print()

# Step 3: Data Storage: Save the cleaned data in a structured format, such as a CSV or a database.
cleaned_csv_file = 'zameenCleanedData.csv'
data.to_csv(cleaned_csv_file, index=False)
print("Cleaned data saved to:", cleaned_csv_file)
print()

# Step 4: Data Analysis: Perform basic exploratory data analysis to gain insights into the collected property data.
import matplotlib.pyplot as plt
# Group the data by 'City' and count the number of properties in each city
property_count_by_city = data['City'].value_counts()
# Create the pie chart using matplotlib
plt.figure(figsize=(10, 6))
plt.pie(property_count_by_city, labels=property_count_by_city.index, autopct='%1.1f%%')
plt.title('Number of properties in each city')
plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
# Show the pie chart
plt.show()

import seaborn as sns
import re
# Define a function to convert the price strings to numerical values
def convert_price_to_numeric(price):
    # Regular expressions to extract numeric values and units from the price strings
    lakhs_pattern = re.compile(r'([\d.]+)\s*Lakh')
    crore_pattern = re.compile(r'([\d.]+)\s*Crore')

    # Convert the price string to a numerical value based on the unit (Lakh or Crore)
    if lakh_match := lakhs_pattern.search(price):
        return float(lakh_match.group(1)) * 100000
    elif crore_match := crore_pattern.search(price):
        return float(crore_match.group(1)) * 10000000
    else:
        return None

# Apply the function to the 'Price' column to convert prices to numeric values
data['Price'] = data['Price'].apply(convert_price_to_numeric)

# Create Visualization for Prices by Cities
# Group the data by 'City' and calculate the count of properties in each price range for each city
bins = [0, 5000000, 10000000, 20000000, 50000000, 1000000000]  # Price bins in rupees
labels = ['< 50 Lakh', '50 Lakh - 1 Crore', '1 Crore - 2 Crore', '2 Crore - 5 Crore', '> 5 Crore']
data['Price Range'] = pd.cut(data['Price'], bins=bins, labels=labels)

# Create a dot plot to visualize the count of properties in different price ranges for each city
plt.figure(figsize=(12, 6))
sns.stripplot(x='Price Range', y='City', data=data, jitter=True, dodge=True, palette='Set1')
plt.xlabel('Price Range')
plt.ylabel('City')
plt.title('Property Prices by City')
plt.tight_layout()

# Show the plot
plt.show()

city_stats = data.groupby('City')['Price'].agg(['mean', 'max', 'min']).reset_index()

#Display the statistics
print("Property Statistics by City:")
print(city_stats)

# Deployment: Provide the client with the scraped and cleaned dataset, along with the web scraper code
# Github Link: https://github.com/MahdiahAqib/Webscrapping-Zameen.com/upload/main

