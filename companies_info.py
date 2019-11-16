from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from lxml import etree
from io import StringIO
from selenium.webdriver.firefox.options import Options
import os, sys, signal, traceback

replacement = {
  "M.": "Monsieur",
  "Mme": "Madame"
}

legalInfoWanted = ["Année de création","Forme juridique","Activités (NAF08)","Capital","SIREN","SIRET (Siège)"]

class CompaniesInfo:

    def __init__(self):
        sys.excepthook = self.myexcepthook
        signal.signal(signal.SIGINT, self.signal_handler)
        self.file = open(sys.path[0] + "/entreprises.csv","w")
        self.file.write("Nom,Adresse,Code postal,Ville,")
        for title in legalInfoWanted:
            self.file.write(title + ",")
        self.file.write("dirigeant,propriété\n")
        print("Starting headless firefox ...")
        options = Options()
        options.add_argument('--headless')
        self.driver = webdriver.Firefox(executable_path=sys.path[0] + '/geckodriver',options=options)
        print("OK. Starting crawling")

    def reset(self):
        print("resetting browser ...")
        self.driver.close()
        options = Options()
        options.add_argument('--headless')
        self.driver = webdriver.Firefox(executable_path=sys.path[0] + '/geckodriver',options=options)

    def signal_handler(self, sig, frame):
        self.driver.quit()
        self.file.close()
        sys.exit(0)

    def myexcepthook(self,type, value, tb):
        self.driver.quit()
        self.file.close()
        traceback.print_exception(type, value, tb)

    def getBasePageInfo(self, suffix):
        print("Retrieving number of pages ...")
        self.driver.get('https://fr.kompass.com/v/' + suffix)
        elem = self.driver.find_elements_by_class_name("pagination")
        children = elem[0].find_elements_by_xpath(".//*")
        maxPage = int(children[len(children)-1].get_attribute('innerHTML').strip())
        i = 1
        print("found " + str(maxPage) + " pages")
        while i <= maxPage:
            print("page " + str(i) + "/" + str(maxPage) + "  ")
            self.getPageCompaniesURL('https://fr.kompass.com/v/' + suffix + 'page-' + str(i))
            i = i + 1

    def getPageCompaniesURL(self, url):
        self.driver.get(url)
        elems = self.driver.find_elements_by_class_name("product-list-data")
        URLList = []
        for elem in elems:
            links = elem.find_elements_by_xpath("./h2/a[contains(@id,'seoCompanyLink')]")
            for link in links:
                #print(link.get_attribute('outerHTML'))
                URLList.append(link.get_attribute('href'))
        print("found " + str(len(URLList)) + " URLs on this page")
        j = 1
        for URL in URLList:
            print("URL " + str(j) + "/" + str(len(URLList)), end = '\r')
            self.getSelectedCompanyInfo(URL)
            j = j + 1
        self.reset()


    def getSelectedCompanyInfo(self, url):
        print("\nwill retrive " + url + "\n")
        self.driver.get(url)
        print(" retrieved url = " + url)
        companyName = self.driver.find_elements_by_xpath(".//div[@class='companyCol1 blockNameCompany']/h1")
        #for company in companyName:
        #    print(company.get_attribute('outerHTML'))
        if(len(companyName) > 0):
            self.file.write('"' + companyName[0].text + '"' + ",")
        else:
            print("\ncouldn't find name\n")
            self.file.write(",")

        elem = self.driver.find_elements_by_class_name("spRight")
        lines = elem[0].text.split("\n")
        i = 0
        self.file.write('"')
        while i < len(lines) - 1:
            self.file.write(lines[i] + " ")
            i = i + 1
        self.file.write('",' + lines[len(lines) - 1].replace(" ",",") + ',')

        elems = self.driver.find_elements_by_xpath(".//div[@class='blockInterieur']")
        for elem in elems:
            #print(elem.get_attribute('outerHTML'))
            legal = elem.find_elements_by_xpath("./table/tbody/tr")
            if(len(legal) > 0):
                legalMap = {}
                for legInfo in legal:
                    legalMap[legInfo.find_elements_by_xpath("./th")[0].text] = legInfo.find_elements_by_xpath("./td")[0].text
                #print(legalMap)
                legalStr = ""
                for key in legalInfoWanted:
                    if key in legalMap:
                        legalStr = legalStr + '"' + legalMap[key] + '"' + ","
                    else:
                        legalStr = legalStr + ","
                self.file.write(legalStr.replace("\nVoir la classification Kompass",""))

            boss = elem.find_elements_by_xpath("./div[@id='executive-info-1']/div/div[@class='executiveText']/p")
            if(len(boss) > 0):
                name = boss[0].text
                for expr in replacement:
                    name = name.replace(expr, replacement[expr])
                self.file.write(name + "," + boss[1].text)
            else:
                if "association" in legalMap["Forme juridique"].lower():
                    self.file.write("A l'attention du président")
                    break
        self.file.write("\n")

info = CompaniesInfo()
info.getBasePageInfo('houdan/fr_11_78_78310/')
info.driver.quit()
info.file.close()


