#imprting modules
import argparse
import requests
import random
from bs4 import BeautifulSoup
from lxml import etree, html
from io import BytesIO
import lxml.html
from PIL import Image
import urllib.request
import pytesseract
import cv2
import time
import json


#class for scrapping lisence data
class DlScrapper:


    #contructor
    def __init__(self, dlnum , dob):

        #initialising variables 
        self.url = 'https://parivahan.gov.in/rcdlstatus/?pur_cd=101'
        self.session = requests.Session()

        self.session.headers['User-Agent']
        
        self.my_headers = [{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"},

                    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "en-US,en;q=0.5"},

                    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "en-IN,en;q=0.7,te;q=0.3"}]

        self.my_header = random.choice(self.my_headers)

        self.dlnum = dlnum
        self.dob = dob

    
    def get_captcha(self, img_src):
        
        #making request for captcha image
        image_response = self.session.get( 'https://parivahan.gov.in' + img_src, headers = self.my_header)
  
        file_like = BytesIO(image_response.content)
        img = Image.open(file_like)     

        #saving image
        img.save('captcha_original.png')
        gray = img.convert('L')
        gray.save('captcha_gray.png')
        bw = gray.point(lambda x: 0 if x < 1 else 255, '1')
        bw.save('captcha_thresholded.png')

        #reading the image in grayscale nd dilating it
        img = cv2.imread('captcha_thresholded.png', cv2.IMREAD_GRAYSCALE)
        cv2.dilate(img,(5,5),img)

        #extracting text from captcha
        text = pytesseract.image_to_string(img, config = '--psm 7')
        final_text = ''
        for character in text:
            if character.isalnum():
                final_text+=character

        return final_text

    def scrape_data(self):

        #this loop runs until the data is scraped 
        while (True):

            try:
            
                print('collecting data...')
                #making request to url
                response = self.session.get(self.url, headers = self.my_header)

                htm = html.fromstring(response.content)

                #ectracting form element using xpath
                form = htm.xpath('/html/body/form')[0]

                action = form.attrib['action'].split(';')[0]

                #extracting viewstate, it is used un subequent requests data 
                viewstate = form.inputs['javax.faces.ViewState'].value
            
                img_src = htm.cssselect('img')[1].get('src')
            
                text = self.get_captcha(img_src)
                print('Trying captcha: '+text)

                capcha = text 

                #four post requests need to be made to get the data

                #data for request 1
                data1 = {'javax.faces.partial.ajax': 'true',
                    'javax.faces.source' : 'form_rcdl:tf_dlNO',
                    'javax.faces.partial.execute': 'form_rcdl:tf_dlNO',
                    'javax.faces.partial.render': 'form_rcdl:tf_dlNO',
                    'javax.faces.behavior.event': 'valueChange',
                    'javax.faces.partial.event': 'change',
                    'form_rcdl': 'form_rcdl',
                    'form_rcdl:tf_dlNO' : self.dlnum,
                    'form_rcdl:tf_dob_input': None, 
                    'form_rcdl:j_idt32:CaptchaID': None,
                    'javax.faces.ViewState': viewstate}

                #making the first request
                result1 = self.session.post('https://parivahan.gov.in'+action, data1, self.my_header)

                #extracting viewstate
                viewstate = result1.text[result1.text.rindex('CDATA')+6 : len(result1.text)-41]
                
                #data to be passed with second request
                data2 = {'javax.faces.partial.ajax': 'true',
                    'javax.faces.source': 'form_rcdl:tf_dob',
                    'javax.faces.partial.execute': 'form_rcdl:tf_dob',
                    'javax.faces.partial.render': 'form_rcdl:tf_dob',
                    'javax.faces.behavior.event': 'valueChange',
                    'javax.faces.partial.event': 'change',
                    'form_rcdl:tf_dob_input': self.dob,
                    'javax.faces.ViewState': viewstate}

                #making 2nd request
                result2 = self.session.post('https://parivahan.gov.in' + action, data2, self.my_header)

                #extracting viewstate
                viewstate = result2.text[result2.text.rindex('CDATA')+6 : len(result2.text)-41]
            
                #data to be passed in third request
                data3 = {'form_rcdl': 'form_rcdl',
                    'form_rcdl:tf_dlNO': self.dlnum,
                    'form_rcdl:tf_dob_input': self.dob,
                    'form_rcdl:j_idt32:CaptchaID': capcha,
                    'javax.faces.ViewState': viewstate,
                    'javax.faces.source': 'form_rcdl:j_idt32:CaptchaID',
                    'javax.faces.partial.event': 'blur',
                    'javax.faces.partial.execute': 'form_rcdl:j_idt32:CaptchaID',
                    'javax.faces.partial.render': 'form_rcdl:j_idt32:CaptchaID',
                    'CLIENT_BEHAVIOR_RENDERING_MODE': 'OBSTRUSIVE',
                    'javax.faces.behavior.event': 'blur',
                    'javax.faces.partial.ajax': 'true'}

                #making 3rd request
                result3 = self.session.post('https://parivahan.gov.in' + action, data3, self.my_header)

                #data to be passed in forth request
                data4 = {'javax.faces.partial.ajax': 'true',
                    'javax.faces.source': 'form_rcdl:j_idt43',
                    'javax.faces.partial.execute': '@all',
                    'javax.faces.partial.render': 'form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl',
                    'form_rcdl:j_idt43' : 'form_rcdl:j_idt43',
                    'form_rcdl': 'form_rcdl',
                    'form_rcdl:tf_dlNO': self.dlnum,
                    'form_rcdl:tf_dob_input': self.dob,
                    'form_rcdl:j_idt32:CaptchaID': capcha,
                    'javax.faces.ViewState': viewstate}

                #making the 4th request
                result4 = self.session.post('https://parivahan.gov.in' + action, data4, self.my_header)
                
                #cheching if the captcha is valid
                if '"validationFailed":true' not in result4.text :
                    
                    xhtml = html.fromstring(result4.content)

                    #extracting required data  
                    current_status = xhtml.cssselect('td')[1].text_content()
                    holders_name = xhtml.cssselect('td')[3].text_content()
                    date_of_issue = xhtml.cssselect('td')[5].text_content()
                    last_transation_at = xhtml.cssselect('td')[7].text_content()
                    validity_details_non_transport_from = xhtml.cssselect('td')[11].text_content()[6:]
                    validity_details_non_transport_to = xhtml.cssselect('td')[12].text_content()[4:]
                    validity_details_transport_from = xhtml.cssselect('td')[14].text_content()[6:]
                    validity_details_transport_to = xhtml.cssselect('td')[15].text_content()[4:]
                    hazardous_valid_till = xhtml.cssselect('td')[17].text_content()
                    hill_valid_till = xhtml.cssselect('td')[19].text_content()

                    #this list will contain all the class_of_vehicles related data
                    class_of_vehicle_details_list = []
                    temp_dict = {}
                    c = 0
                    for i in xhtml.cssselect('td')[20:]:
                        if c==0:
                            temp_dict['cov_category'] = i.text_content()
                        elif c==1:
                            temp_dict['class_of_vehicle'] = i.text_content()
                        else:
                            temp_dict['cov_issue_date'] = i.text_content()
                        
                        c=c+1
                        c= c% 3
                        if c==0:
                            class_of_vehicle_details_list.append(temp_dict)
                            temp_dict = {}

                    #this dictionary holds the final result
                    data = {'Current_Status' : current_status,
                    'holders_name' : holders_name,
                    'date_of_issue' : date_of_issue,
                    'last_transaction_at' : last_transation_at,

                    'driving_licence_validity_details' : {'non_transport':{'from' : validity_details_non_transport_from, 'to' : validity_details_non_transport_to },
                                                        'transport':{'from' : validity_details_transport_from, 'to' : validity_details_transport_to },
                                                        'hazardous_valid_till': hazardous_valid_till,
                                                        'hill_valid_till' : hill_valid_till },
                    'class_of_vehicle_details': class_of_vehicle_details_list

                    }

                    #returning data in json format
                    return json.dumps(data, indent = 4)
                
                else:
                    print('Captcha failed, retrying.....')

                #waiting between requests
                time.sleep(2)

                
            except Exception as e:
                print(e)

if __name__ == '__main__':

    # Create the parser
    parser = argparse.ArgumentParser(description='lisence number and date of birth')

    # Add the arguments
    parser.add_argument('--dlnum',                      
                        type=str,
                        help='Enter driver lisence number')

    parser.add_argument('--dob',                      
                        type=str,
                        help='Enter date of birth')

    # Execute the parse_args() method
    args = parser.parse_args()

    dlscrapper = DlScrapper(args.dlnum, args.dob)
    data = dlscrapper.scrape_data()
    print(data)
    
    


