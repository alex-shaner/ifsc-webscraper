from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import numpy as np
import time
import datetime


class IFSCScraper():
    """
    Define a class for the scraper that will be used to gather data from the IFSC website
    (ifsc-climbing.org)
    Includes methods that allow for scraping different pages and different information
    """

    def __init__(self, debug=False):
        """
        Initialize a scraper object with its own browser instance
        Input:
            debug - Indicates whether this is a debug instance for quicker development
        """

        self.debug = debug

        # Add incognito arg to webdriver
        option = webdriver.ChromeOptions()
        option.add_argument(" — incognito")

        #prevent chrome push notifications which interrupt scraper
        prefs = {"profile.default_content_setting_values.notifications" : 2}
        option.add_experimental_option("prefs",prefs)

        # Create new instance of Chrome
        self.browser = webdriver.Chrome(options=option)

        time.sleep(1)


    def get_last_result_html(self):
        """
        Returns the html for the world competition last result page
        We will use this page to find more detailed information about recent competitions
        input:
            N/A
        output:
            html of the world competition last result page
        """

        # Page url
        url = 'https://www.ifsc-climbing.org/index.php/world-competition/last-result'

        self.load_page(url)


    def get_comp_data(self):
        """
        Parse the world-competition/last-result page to find and return a list of comps and their data
        input:
            N/A
        output:
            List of touples containing comp names, dates, and lists for each data type (lead, speed, boulder, combined)
        """

        # Page url
        url = 'https://www.ifsc-climbing.org/index.php/world-competition/last-result'

        self.load_page(url)

        # Store iframe web element
        iframe = self.browser.find_element(By.TAG_NAME, "iframe")
        # switch to selected iframe
        self.browser.switch_to.frame(iframe)

        #store selector elements
        yearsSelector = self.browser.find_element(By.ID, "years")
        leagueSelector = self.browser.find_element(By.ID, "indexes")
        compSelector = self.browser.find_element(By.ID, "events")
        catSelector = self.browser.find_element(By.ID, "categories")

        yearOptions = yearsSelector.find_elements(By.TAG_NAME, "option")
        comps = []

        for year in yearOptions:
            today = datetime.date.today()
            currentYear = today.year
            if year.text == str(currentYear+1):
                continue

            if year.text == "2019":
                break

            year.click()
            time.sleep(3)
            leagues = []
            leagueOptions = leagueSelector.find_elements(By.TAG_NAME, "option")

            for league in leagueOptions:
                if league.text == "Select league":
                    continue

                leagues.append(league.text)
                league.click()
                time.sleep(2)

                #conditional because I don't have time to so anything other than world cup
                if "IFSC" in league.text:
                    break

                
                compOptions = compSelector.find_elements(By.TAG_NAME, "option")

                for comp in compOptions:   
                    if comp.text == "Select event":
                        continue
                    if "CANCELLED" in comp.text:
                        continue

                    comp.click()
                    time.sleep(3)

                    name = self.browser.find_element(By.CLASS_NAME, "event_title").text
                    date = self.browser.find_element(By.CLASS_NAME, "event_date").text
                    lead_data = []
                    speed_data = []
                    boulder_data = []
                    combined_data = []
                  
                    catOptions = catSelector.find_elements(By.TAG_NAME, "option")

                    for cat in catOptions:
                        if cat.text == "Select category":
                            continue

                        #since we just want boulder data for now, adding this conditional
                        if "BOULDER" not in cat.text:
                            continue


                        prior_info = (name, date, cat.text)
                        if "&" in cat.text:
                            cat.click()                            
                            combined_data.append(self.get_data_on_page(prior_info))
                            
                        elif "SPEED" in cat.text:
                            cat.click()                            
                            speed_data.append(self.get_data_on_page(prior_info))
                            
                        elif "BOULDER" in cat.text:
                            cat.click()                            
                            boulder_data.append(self.get_data_on_page(prior_info))
                            
                        elif "LEAD" in cat.text:
                            cat.click()                            
                            lead_data.append(self.get_data_on_page(prior_info))
                            

                    comps.append(boulder_data)
                    #comps.append([lead_data, speed_data, boulder_data, combined_data])
                        
        return comps
    

    def make_df_from_data(self, comp_data):
        """
        Takes the scraped data available in list format and converts it to dataframes
        input:
            comp_data: List of lists of tuples specifying competition results for different categories
        output:
            List of dataframes containing data
        """
        #lead_data, speed_data, boulder_data, combined_data = comp_data[0]
        boulder_data = comp_data

        # Create lead df
        #lead_df = self.build_df(lead_data)

        # Create speed df
        #speed_df = self.build_df(speed_data)

        # Create boulder df
        boulder_df = self.build_df(boulder_data)

        # Create combined df
        #combined_df = self.build_df(combined_data)

        #just boulder for now
        #return [lead_df, speed_df, boulder_df, combined_df]
        return [boulder_df]

    def build_df(self, cat_data):
        """
        Given the data for a category, build a df for it
        input:
            cat_data - Data scraped for a particular category
        output:
            df of the data
        """
        # Iterate through competitions, build list of dicts for df
        data_list = []
        print (cat_data)


        for comp in cat_data:
            # Iterate through results per comp
            for result in comp:
                # Convert to dict
                print(result)
                this_dict = dict(result)
                data_list.append(this_dict)
        
        # Convert to df
        df = pd.DataFrame(data_list)

        return df


    def get_data_on_page(self, prior_info):
        """
        Helper function that scrapes the data from a complete result page and returns it in a tuple
        input:
            prior_info - Comp name, date, subcategory
        output:
            touple representing the table of results on the page
        """

        #bonus sleep because ifsc webservers suck ass I guess
        WebDriverWait(self.browser, 20).until(EC.visibility_of_element_located((By.ID, "table_id")))
        
        # Get table from webpage
        resultTable = self.browser.find_element(By.ID, "table_id")
        
        # Get headers
        result_headers = resultTable.find_elements(By.TAG_NAME, 'th')
        headers = [x.text for x in result_headers]
        
        print("\n\n" +str(prior_info))
        # Fix name
        headers[1] = 'FIRST'
        headers[2] = 'LAST'
        print(str(headers))
        
        # Get table rows
        rows = resultTable.find_elements(By.TAG_NAME, 'tr')
        #skip the header row
        rows = rows[1:]

        # Package data to be returned
        ret_data = []

        # Split rows into tuples and add to list
        for row in rows:
            rowElements = row.find_elements(By.TAG_NAME, 'td')
            rowContent = [x.text for x in rowElements]
            add_this = [("Competition Title", prior_info[0]), ("Competition Date", prior_info[1]), ("Category", prior_info[2])] + [(header, x) for header, x in zip(headers, rowContent)]
            ret_data.append(add_this)

        print(ret_data)
        return ret_data

    def load_page(self, link, timeout=20, wait_after=10):
        """
        Helper function that loads a page and waits for timeout
        input:
            link - Link to the page we wish to load
            timeout - Seconds to wait before timing out
            wait_after - Seconds to wait after loading
        output:
            N/A
        """

        # Visit link
        self.browser.get(link)

        # Attempt to open link
        try:
            WebDriverWait(self.browser, timeout).until(EC.visibility_of_element_located((By.XPATH,
            "//div[@class='uk-section-primary uk-section uk-section-xsmall']")))
        except TimeoutException:
            print("Timed out waiting for page " + link + " to load")
            self.browser.quit()

        # Wait for page to load
        time.sleep(wait_after)

    def merge_dfs(self, gathered_dfs):
        """
        Merge newly gathered dfs with old dfs
        input:
            gathered_dfs - pandas dataframes that have been gathered this run
        output:
            merged dfs
        """
        # Split into dfs
        lead_df, speed_df, boulder_df, combined_df = gathered_dfs

        # Merge each df with the exisiting data
        old_lead_df = pd.read_csv('~/projects/ifsc-scraper/data/lead_results.csv')
        old_speed_df = pd.read_csv('~/projects/ifsc-scraper/data/speed_results.csv')
        old_boulder_df = pd.read_csv('~/projects/ifsc-scraper/data/boulder_results.csv')
        old_combined_df = pd.read_csv('~/projects/ifsc-scraper/data/combined_results.csv')

        lead_df = pd.concat([lead_df, old_lead_df], ignore_index=True)
        speed_df = pd.concat([speed_df, old_speed_df], ignore_index=True)
        boulder_df = pd.concat([boulder_df, old_boulder_df], ignore_index=True)
        combined_df = pd.concat([combined_df, old_combined_df], ignore_index=True)

        return [lead_df, speed_df, boulder_df, combined_df]

    def clean_boulder(self, boulder_df):
        """
        Cleans up the columns of the boulder df
        input:
            boulder_df - pandas dataframe containing info about bouldering comps
        output:
            cleaned boulder df
        """
        # Names of the possible columns for semifinals
        semifinal_cols = ['Semi-Final', 'Semi Final', 'Semifinal', 'semi-Final', 'SemiFinal',
        'Semi final', 'Semi-final', 'Semi - Final', '1/2-Final']

        # Remove column names that aren't in this df
        for col in list(semifinal_cols):
            if col not in list(boulder_df):
                semifinal_cols.remove(col)

        # Consolidate columns
        boulder_df['New Semifinal'] = boulder_df[semifinal_cols].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis=1
        )
        boulder_df = boulder_df.drop(semifinal_cols, axis=1)
        boulder_df = boulder_df.rename(columns={'New Semifinal':'Semifinal'})

        # Qualification 1 columns
        qual_cols = ['1. Qualification (2)', '1. Qualification', 'Qualification (Group 1)',
                 'Qualification (group A)', 'A Qualification', 'A. Qualification',
                 'Qualification A', 'Qualification Group A', 'Qualification 1']

        # Remove column names that aren't in this df
        for col in list(qual_cols):
            if col not in list(boulder_df):
                qual_cols.remove(col)

        # Consolidate columns
        boulder_df['New Qualification 1'] = boulder_df[qual_cols].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis=1
        )
        boulder_df = boulder_df.drop(qual_cols, axis=1)
        boulder_df = boulder_df.rename(columns={'New Qualification 1':'Qualification 1'})


        # Qualification 2 columns
        qual_cols = ['2. Qualification (2)', '2. Qualification', 'Qualification (Group 2)',
                 'B Qualification', 'Qualification (group B)', 'B. Qualification',
                 'Qualification B', 'Qualification Group B', 'Qualification 2']

        # Remove column names that aren't in this df
        for col in list(qual_cols):
            if col not in list(boulder_df):
                qual_cols.remove(col)

        # Consolidate columns
        boulder_df['New Qualification 2'] = boulder_df[qual_cols].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis=1
        )
        boulder_df = boulder_df.drop(qual_cols, axis=1)
        boulder_df = boulder_df.rename(columns={'New Qualification 2':'Qualification 2'})


        return boulder_df

    def clean_combined(self, combined_df):
        """
        Cleans up the columns of the combined df
        input:
            combined_df - pandas dataframe containing info about combined comps
        output:
            cleaned combined df
        """
        # No cleaning needed as of 10/16/2019
        return combined_df

    def clean_lead(self, lead_df):
        """
        Cleans up the columns of the lead df
        input:
            lead_df - pandas dataframe containing info about lead comps
        output:
            cleaned lead df
        """

        # Names of the possible columns for semifinals
        semifinal_cols = ['1/2 Final', 'Semi-Final', 'Semi Final', 'SemiFinal', 'Semi-final', '1/2 - Final', '1/2-Final', 'Semi - Final', 'Semifinal']

        # Remove column names that aren't in this df
        for col in list(semifinal_cols):
            if col not in list(lead_df):
                semifinal_cols.remove(col)
        
        # Consolidate columns
        lead_df['New Semifinal'] = lead_df[semifinal_cols].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis=1
        )
        lead_df = lead_df.drop(semifinal_cols, axis=1)
        lead_df = lead_df.rename(columns={'New Semifinal':'Semifinal'})

        # Names of the possible columns for qualification 1
        qual_cols = ['1. Qualification 1', '1. Qualification',
        'Qualification 1', '1. Qualification:', '1.Qualification',
        'Group A Qualification', '1 Qualification', 'Qualification 1']
        
        # Remove column names that aren't in this df
        for col in list(qual_cols):
            if col not in list(lead_df):
                qual_cols.remove(col)

        # Consolidate columns
        lead_df['New Qualification'] = lead_df[qual_cols].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis=1
        )
        lead_df = lead_df.drop(qual_cols, axis=1)
        lead_df = lead_df.rename(columns={'New Qualification':'Qualification 1'})
        
        # Names of the possible columns for qualification 2
        qual_cols = ['2. Qualification', '2. Qualification 2', 'Qualification 2', 'Group B Qualification', 'Qualification 2']

        # Remove column names that aren't in this df
        for col in list(qual_cols):
            if col not in list(lead_df):
                qual_cols.remove(col)

        lead_df['New Qualification'] = lead_df[qual_cols].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis=1
        )
        lead_df = lead_df.drop(qual_cols, axis=1)
        lead_df = lead_df.rename(columns={'New Qualification':'Qualification 2'})

        # Drop this random nan column is it's there
        try:
            lead_df = lead_df.drop(['Unnamed: 18'], axis=1)
        except:
            pass

        return lead_df

    def clean_speed(self, speed_df):
        """
        Cleans up the columns of the speed df
        input:
            speed_df - pandas dataframe containing info about speed comps
        output:
            cleaned speed df
        """

        # Names of the possible columns for 1/8 finals
        eighths = ['1/8 - Final', '1_8 - Final']

        # Remove column names that aren't in this df
        for col in list(eighths):
            if col not in list(speed_df):
                eighths.remove(col)

        speed_df['New Eighths'] = speed_df[eighths].apply(
            lambda x: ','.join(x.dropna().astype(str)),
            axis=1
        )
        speed_df = speed_df.drop(eighths, axis=1)
        speed_df = speed_df.rename(columns={'New Eighths':'1/8 - Final'})

        return speed_df

    def scrape(self):
        """
        Scrape the website, build dataframes, save dataframes
        input:
            N/A
        output:
            N/A
        """

        #just boulder for now
        #lead_df, speed_df, boulder_df, combined_df = self.make_df_from_data(self.get_comp_data())
        boulder_df = self.make_df_from_data(self.get_comp_data())

        # Merge new data with old data
        #lead_df, speed_df, boulder_df, combined_df = self.merge_dfs([lead_df, speed_df, boulder_df, combined_df])

        # Clean data before saving
        #lead_df = self.clean_lead(lead_df)
        #speed_df = self.clean_speed(speed_df)
        #boulder_df = self.clean_boulder(boulder_df)
        #combined_df = self.clean_combined(combined_df)

        #lead_df.to_csv('lead_results.csv', index=False)
        #speed_df.to_csv('speed_results.csv', index=False)
        boulder_df.to_csv('boulder_results.csv', index=False)
        #combined_df.to_csv('combined_results.csv', index=False)


def main():
    # Create scraper object
    scraper = IFSCScraper()

    # Run scraper
    scraper.scrape()

if __name__ == '__main__':
    main()