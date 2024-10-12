# %% [markdown]
# #### Initial Imports and Constants

# %%
import pandas as pd
import requests
import concurrent.futures
from tqdm import tqdm
import cloudscraper

scraper = cloudscraper.create_scraper()

# %%
headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI4YjI0ZTQ0MC1lM2RiLTQzMGItYjdkMS0xZDEyZGZmMTMxZjQ6MDY4OTI4ZmYtZTlkYi00NGEwLTllMDktZmZkOGIxMjEzMWM4IiwiYWNjb3VudF9rZXkiOiI4YjI0ZTQ0MC1lM2RiLTQzMGItYjdkMS0xZDEyZGZmMTMxZjQiLCJ1c2VyX2tleSI6IjA2ODkyOGZmLWU5ZGItNDRhMC05ZTA5LWZmZDhiMTIxMzFjOCIsIm5hbWUiOiJSYWZmaWUiLCJlbWFpbCI6InJhZmZpZUBjb21tZXJjaWFsc3BhY2Vob3VzdG9uLmNvbSIsImlhdCI6MTcxODk4NDEyMCwiZXhwIjoyMTQ3NDcyMDAwfQ.y6JGNIagBaq57YJdKxsz4jp2YGHHAu9byT9DjRg9sOU"
}

# %% [markdown]
# #### Getting Contact Records

# %%
def get_properties():
    """
    Fetch properties from the RealNex CRM API using multithreading for efficiency.

    This function fetches properties from the RealNex CRM API by making multiple concurrent requests.
    It handles pagination and collects all the data into a single list of DataFrames.

    Returns:
        list of pd.DataFrame: A list where each element is a DataFrame containing contact data from a single API response page.

    Nested Functions:
        fetch_page(page):
            Fetch a single page of properties from the API.

            Args:
                page (int): The page offset for the API request.

            Returns:
                pd.DataFrame: A DataFrame containing the properties data from the API response.
    """
    def fetch_page(page):
        """
        Fetch a single page of properties from the RealNex CRM API.

        Args:
            page (int): The page offset for the API request.

        Returns:
            pd.DataFrame: A DataFrame containing the properties data from the API response.
        """        
        url = f'https://sync.realnex.com/api/v1/CrmOData/Properties?api-version=1.0&$skip={page}'
        payload= {}
        response = requests.get(url, headers=headers, data=payload)
        return pd.DataFrame(response.json()['value'])

    temp_list = []
    page = 0
    limit = 1  # Initialize limit to enter the while loop

    with concurrent.futures.ThreadPoolExecutor() as executor:
        while limit != 0:
            future_to_page = {executor.submit(fetch_page, page): page for page in range(page, page + 500, 50)}
            for future in concurrent.futures.as_completed(future_to_page):
                data = future.result()
                limit = len(data)
                if limit > 0:
                    temp_list.append(data)
            page += 500  # Increment by 500 because we are fetching 10 pages in parallel
            
    return pd.concat(temp_list, ignore_index=True)

    temp_list = []
    page = 0
    limit = 1  # Initialize limit to enter the while loop

    with concurrent.futures.ThreadPoolExecutor() as executor:
        while limit != 0:
            future_to_page = {executor.submit(fetch_page, page): page for page in range(page, page + 500, 50)}
            for future in concurrent.futures.as_completed(future_to_page):
                data = future.result()
                limit = len(data)
                if limit > 0:
                    temp_list.append(data)
            page += 500  # Increment by 500 because we are fetching 10 pages in parallel
            
    return pd.concat(temp_list, ignore_index=True)

# %%
def get_contacts():
    """
    Fetch contacts from the RealNex CRM API using multithreading for efficiency.

    This function fetches contacts from the RealNex CRM API by making multiple concurrent requests.
    It handles pagination and collects all the data into a single list of DataFrames.

    Returns:
        list of pd.DataFrame: A list where each element is a DataFrame containing contact data from a single API response page.

    Nested Functions:
        fetch_page(page):
            Fetch a single page of contacts from the API.

            Args:
                page (int): The page offset for the API request.

            Returns:
                pd.DataFrame: A DataFrame containing the contacts data from the API response.
    """
    def fetch_page(page):
        """
        Fetch a single page of contacts from the RealNex CRM API.

        Args:
            page (int): The page offset for the API request.

        Returns:
            pd.DataFrame: A DataFrame containing the contacts data from the API response.
        """        
        url = f'https://sync.realnex.com/api/v1/CrmOData/Contacts?api-version=1.0&$skip={page}'
        payload= {}
        response = requests.get(url, headers=headers, data=payload)
        return pd.DataFrame(response.json()['value'])

    temp_list = []
    page = 0
    limit = 1  # Initialize limit to enter the while loop

    with concurrent.futures.ThreadPoolExecutor() as executor:
        while limit != 0:
            future_to_page = {executor.submit(fetch_page, page): page for page in range(page, page + 500, 50)}
            for future in concurrent.futures.as_completed(future_to_page):
                data = future.result()
                limit = len(data)
                if limit > 0:
                    temp_list.append(data)
            page += 500  # Increment by 500 because we are fetching 10 pages in parallel
            
    return pd.concat(temp_list, ignore_index=True)

# %% [markdown]
# ##### Testing get contact function

# %%
if __name__ == '__main__':
    contacts_df = get_contacts()

# %%
    contacts_df.to_csv("actual imported contacts in realnex.csv", index=False)

# %% [markdown]
# #### Uploading Notes

# %%
def add_notes(contact_key, date, subject, notes):
    """
    Adds notes to a contact's history in the RealNex CRM.

    Parameters:
    contact_key (str): The unique identifier for the contact.
    date (str): The date for the note in 'Y-m-d' format.
    subject (str): The subject of the note.
    notes (str): The detailed notes to be added.

    Returns:
    response (requests.Response): The response from the RealNex API after posting the note.
    """
    data = {
            "eventTypeKey": 18,
            "published":True,
            "timeless":True,
            "startDate": date,
            "endDate": date,
            "subject": subject,
            "notes": notes,
            "statusKey": 0
    }

    url = f'https://sync.realnex.com/api/v1/Crm/object/{contact_key}/history'
    response = scraper.post(url, headers=headers, json=data)

    return response

def get_notes(input_list):
    """
    Getting notes in realnex

    response (requests.Response): The response from the RealNex API after posting the note.
    """

    def fetch_data(contact_id):
        url = f'https://sync.realnex.com/api/v1/Crm/object/{contact_id}/history'
        response = scraper.get(url, headers=headers)
        return pd.DataFrame(response.json()['items'])

    temp_list = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_data, contact_id) for contact_id in input_list]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Fetching data"):
            try:
                temp_list.append(future.result())
            except Exception as e:
                print(f"An error occurred: {e}")

    # Combine all DataFrames into one
    final_df = pd.concat(temp_list, ignore_index=True)

    return final_df

def delete_notes(input_list):

    def fetch_data(note_id):
        url = f'https://sync.realnex.com/api/v1/Crm/history/{note_id}'
        response = scraper.delete(url, headers=headers)

    # temp_list = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_data, contact_id) for contact_id in input_list]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Fetching data"):
            try:
                # temp_list.append(future.result())
                pass
            except Exception as e:
                print(f"An error occurred: {e}")


# %% [markdown]
# ##### Testing adding notes function

# %%
if __name__ == '__main__':
    contact_key = contacts_df[contacts_df['FullName'] == 'Raffie Nel Navaluna']['Key'].values[0]
    date = '2024-07-12'
    subject = 'testing api function'
    notes = 'this is notes input in function'

    # calling function
    add_notes(contact_key, date, subject, notes)


# %% [markdown]
# #### Delete contact function

# %%
def delete_contact(contact_key):
    url = f'https://sync.realnex.com/api/v1/Crm/contact/{contact_key}'
    response = scraper.delete(url, headers=headers)

    return response    

# %% [markdown]
# ##### Testing delete contact function

# %%
if __name__ == '__main__':
    contact_delete = pd.read_csv("Realnex Duplicated Contact for Delete.csv")
    contact_delete

    # %%
    for id in contact_delete['Key']:
        resp = delete_contact(id)
        print(id, resp)

    # %%
    contact_delete

    # %%



