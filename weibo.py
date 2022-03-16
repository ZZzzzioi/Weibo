import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import datetime
import yagmail
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

#时间跨度为09年至21年
def open_web_1():
    #使用selenium模拟登陆微博以实现自动搜索功能
    #此前直接使用get可以打开网页，后来打开总是502，可能与网络有关，需要手动在打开的网页上刷新才可进去，或更换网络
    driver = webdriver.Chrome()
    driver.get('https://weibo.com/')
    time.sleep(10)
    return driver

def open_web_2(driver):
    driver.find_element_by_id('loginname').send_keys('18309144368')  #输入微博账号
    time.sleep(5)
    driver.find_element_by_name('password').send_keys('Iieng@9737')  #输入微博密码,偶尔需要填写验证码
    driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()  #登录，后续仍需要进行手机扫码验证    
    time.sleep(50)
    driver.find_element_by_xpath('//*[@id="plc_top"]/div/div/div[2]/a').click() #点击搜索
    time.sleep(5)
    return driver


def keyword_search(driver, time_start, time_end, keyword):
    time.sleep(10)
    driver.find_element_by_xpath('//*[@id="pl_feedtop_top"]/div[3]/a').click()  #点击高级搜索
    driver.find_element_by_xpath('/html/body/div[7]/div[2]/div/div[1]/dl[1]/dd/input').clear() #清空搜索栏
    time.sleep(2)
    driver.find_element_by_id('radio03').click()
    driver.find_element_by_xpath('/html/body/div[7]/div[2]/div/div[1]/dl[1]/dd/input').send_keys(keyword) #关键词，可替换为先前准备好的关键词
    js = "document.getElementsByName('stime')[0].removeAttribute('readonly')" 
    driver.execute_script(js)
    driver.find_element_by_name('stime').clear()
    driver.find_element_by_name('stime').send_keys(time_start) #此处日期后续更换
    time.sleep(1)
    js = "document.getElementsByName('startHour')[0].removeAttribute('disabled')"
    driver.execute_script(js)
    element_1 = driver.find_element_by_xpath('/html/body/div[7]/div[2]/div/div[1]/dl[4]/dd/select[1]')
    Select(element_1).select_by_value('0')
    time.sleep(1)
    js = "document.getElementsByName('etime')[0].removeAttribute('readonly')" 
    driver.execute_script(js)
    driver.find_element_by_name('etime').clear()
    driver.find_element_by_name('etime').send_keys(time_end) #此处日期后续更换
    time.sleep(1)
    js = "document.getElementsByName('endHour')[0].removeAttribute('disabled')"
    driver.execute_script(js)
    element_2 = driver.find_element_by_xpath('/html/body/div[7]/div[2]/div/div[1]/dl[4]/dd/select[2]')
    Select(element_2).select_by_value('0')
    time.sleep(2)
    driver.find_element_by_class_name('s-btn-a').click() #点击搜索
    return driver #返回搜索界面的driver

def changedate(driver, dateset, date_count):
    driver.find_element_by_xpath('//*[@id="pl_feedtop_top"]/div[3]/a').click()  #点击高级搜索
    start = dateset[date_count]
    end = dateset[date_count + 1]
    #设置搜索时长，以天为单位进行搜索，微博的时间选择控件不支持直接填写，使用js将其转为可改写
    js = "document.getElementsByName('stime')[0].removeAttribute('readonly')" 
    driver.execute_script(js)
    driver.find_element_by_name('stime').clear()
    driver.find_element_by_name('stime').send_keys(start) #此处日期后续更换
    time.sleep(1)
    js = "document.getElementsByName('etime')[0].removeAttribute('readonly')" 
    driver.execute_script(js)
    driver.find_element_by_name('etime').clear()
    driver.find_element_by_name('etime').send_keys(end) #此处日期后续更换
    time.sleep(2)
    driver.find_element_by_class_name('s-btn-a').click() #点击搜索
    return driver


def get_content(driver):
    page_count = 1
    card_list = []
    while page_count < 51:  #最大页数为50页，设置循环限定为51
        js = """
        elements = document.getElementsByClassName('txt');
        for (var i=0; i < elements.length; i++)
        {
            elements[i].style.display='block'
        }
        """
        driver.execute_script(js)
        try:
            count = 1
            card_wrap_all = driver.find_elements_by_css_selector("[action-type = 'feed_list_item']")
            for i in card_wrap_all:
                card = []
                card.append(i.find_element_by_css_selector('.name').text) #微博发布者
                card.append(i.find_element_by_css_selector('.name').get_attribute('href')) #微博发布者链接
                #正文
                try:
                    card.append(i.find_element_by_css_selector("[node-type = 'feed_list_content_full']").text)
                except:
                    card.append(i.find_element_by_css_selector("[node-type = 'feed_list_content']").text)
                #时间
                date = i.find_element_by_css_selector('.from')
                card.append(date.find_element_by_css_selector("[target = '_blank']").text)
                #转发数、评论数和点赞数
                card.append(driver.find_element_by_xpath('//*[@id="pl_feedlist_index"]/div[2]/div['+str(count)+']/div/div[2]/ul/li[2]/a').text)
                card.append(driver.find_element_by_xpath('//*[@id="pl_feedlist_index"]/div[2]/div['+str(count)+']/div/div[2]/ul/li[3]/a').text)
                card.append(driver.find_element_by_xpath('//*[@id="pl_feedlist_index"]/div[2]/div['+str(count)+']/div/div[2]/ul/li[4]/a/em').text)
                card_list.append(card)
                count += 1
            driver.find_element_by_class_name('next').click() #下一页
            page_count += 1
            time.sleep(2)     #受网络影响调整
        except: #后续此处重构为改写时间间隔
            break
    return card_list,driver



def date_make(time_start, time_end):
    dateset = pd.date_range(start=time_start, end=time_end) #设定爬取的时间跨度
    dateset_str = dateset.strftime('%Y-%m-%d')
    return dateset_str

def loginfun():
    driver = webdriver.Chrome()
    driver.get('https://weibo.com/')
    time.sleep(20)   
    return driver
      
def save_csv_user(userinfos):
    name = ['居住地', '关注数', '粉丝数', '微博数']
    userinfos_csv = pd.DataFrame(columns = name, data = userinfos)
    #content_list_csv.to_csv('C:/CodeStorage/PY_Code/spider/weibodata_新型冠状病毒_1-40.csv', encoding = 'UTF-8')
    userinfos_csv.to_csv('C:/CodeStorage/PY_Code/spider/WeiboUserData.csv', encoding = 'UTF-8')


def save_csv(content_list):
    name = ['微博发布者', '微博发布者链接', '微博内容', '时间', '转发数','评论数', '点赞数']
    content_list_csv = pd.DataFrame(columns = name, data = content_list)
    #content_list_csv.to_csv('C:/CodeStorage/PY_Code/spider/weibodata_新型冠状病毒_1-40.csv', encoding = 'UTF-8')
    content_list_csv.to_csv('C:/CodeStorage/PY_Code/spider/weibodata_3.csv', encoding = 'UTF-8')  #存储地址，此处需要更改

def sendmail(filename_address):
    receiver = 'jizisheng@foxmail.com'
    body = '代码运行完成'
    filename = filename_address
    yag = yagmail.SMTP(
        user = '2379466557@qq.com',
        password = 'twnsubqmnifoecdj',
        host = 'smtp.qq.com'
    )

    yag.send(
        to = receiver,
        subject = '代码运行完成',
        contents = body,
        attachments = filename
    )


def main():
    driver = open_web_1()
    driver_login = open_web_2(driver)
    content_lists = []
    event = ['医患关系', '2009-08-16', '2021-01-02'] 
    dateset = date_make(event[-2], event[-1])
    driver_search = keyword_search(driver_login, dateset[0], dateset[1], event[0])
    try:
        for date_count in range(1, len(dateset)-1): #len(dateset)-1
            card_list, driver_search = get_content(driver_search)
            try:
                driver_search = changedate(driver_search, dateset, date_count)
            except:
                driver.refresh()
            content_lists += card_list
            print(date_count)
        save_csv(content_lists)
    except:
        save_csv(content_lists)
    #driver = loginfun()
    #time.sleep(40)
    #userinfos = search_user(driver)
    #save_csv_user(userinfos)
    #sendmail('C:/CodeStorage/PY_Code/spider/WeiboUserData.csv')

if __name__ == '__main__':
    main()