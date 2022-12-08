import os
import re
import cv2
import pymysql
import numpy as np
import shutil

from PIL import Image
from pytesseract import *

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from pytube import YouTube
from bs4 import BeautifulSoup
import time
import random

#상수 #FRAME > HAVETEXT > CONTOURS > FFT
VIDEO_DOWNLOAD_FOLDER = '.'+os.sep+'VideoFile'+os.sep # ./VideoFile/
FRAME_SAVE_FOLDER = '.'+os.sep+'Frame'+os.sep # ./Frame/
CONTOURS_SAVE_FOLDER = '.'+os.sep+'Contours'+os.sep # ./Contours/
FFT_SAVE_FOLDER = '.'+os.sep+'FFT'+os.sep # ./FFT/
HAVETEXT_SAVE_FOLDER = '.'+os.sep+'HaveText'+os.sep # ./HaveText/
ClEAN_SAVE_FOLDER = '.'+os.sep+'Clean'+os.sep # ./Clean/

def createDirectory(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print("Error: Failed to create the directory.")

def getfolderPath(path):
    folder_list = os.listdir(path)
    folderPath_list = []
    for i in folder_list :
        k = path + i
        folderPath_list.append(k)
    return folderPath_list

def getFilePathandName(parent) :
    try :
        file_list = os.listdir(parent)
        file_list = [file for file in file_list if file.endswith(".jpg") or file.endswith(".mp4")]
        file_path_dict = {}
        file_name_list = []
        for i in file_list :
            name = i[:-4]
            path = parent + i
            file_name_list.append(name)
            file_path_dict[name] = path
        return file_name_list,file_path_dict
    except NotADirectoryError as e:
        print(e)

def ImageClear(image) :
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    image_sharp = cv2.filter2D(image, -1, kernel)
    return image_sharp

def ColorEqualization(image) :
    image_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    image_yuv[:,:,0] = cv2.equalizeHist(image_yuv[:,:,0])
    image_rgb = cv2.cvtColor(image_yuv, cv2.COLOR_YUV2RGB)
    return image_rgb

def MonoEqualization(image):
    image_enhanced = cv2.equalizeHist(image)
    return image_enhanced

def ocrtostr(full_path, lang='kor'):
    img = Image.open(full_path)#이미지 경로
    #추출
    outText = image_to_string(img, lang=lang, config= '--psm 1 -c preserve_interword_spaces=25')
    #preserve_interword_spaces : 단어 간격 옵션을 조절하면서 추출 정확도를 확인
    #psm = 페이지 세그먼트 모드.
    return outText

def scroll(number):
    if(number != 'True' or 'true') :
        try:
            last_page_height = driver.execute_script("return document.documentElement.scrollHeight")
            for i in range(0, int(number)) :
                pause_time = random.uniform(1, 2)
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(pause_time)
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight-50)")
                time.sleep(pause_time)
                new_page_height = driver.execute_script("return document.documentElement.scrollHeight")
                if new_page_height == last_page_height:
                    print("스크롤 완료")
                else:
                    last_page_height = new_page_height
        except Exception as e:
            print("에러 발생: ", e)
    else :
        try:
            last_page_height = driver.execute_script("return document.documentElement.scrollHeight")
            while True:
                pause_time = random.uniform(1, 2)
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(pause_time)
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight-50)")
                time.sleep(pause_time)
                new_page_height = driver.execute_script("return document.documentElement.scrollHeight")
                if new_page_height == last_page_height:
                    print("스크롤 완료")
                    break
                else:
                    last_page_height = new_page_height
        except Exception as e:
            print("에러 발생: ", e)

def remove_emojis(inputString):
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U0001F900-\U0001F9FF"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    string = re.sub(emoj, '', inputString)
    removed_text = re.sub('[\{\}\[\]\/?.,;:|\)*~`!^\-_+<>@\#$%&\\\=\(\'\"\ㅣ“”•「」【】…｜┃]',
                          '', string)
    removed_text = removed_text.replace(" ", "")
    return removed_text

def extract_frame(path, video, perFPS, length) :

    count = 0
    next_frame = int(perFPS)

    while (video.isOpened()):
        ret, image = video.read()
        j = int(video.get(cv2.CAP_PROP_POS_FRAMES))
        if (j % (perFPS) == 0) :  # fps당 하나씩 키프레임 추출
            savepath = path + "_frame%d.jpg" % count
            cv2.imwrite(savepath, image)
            count += 1
            next_frame += int(perFPS)

            if next_frame > int(length):
                break
        else:
            j += 1
    video.release()

createDirectory(VIDEO_DOWNLOAD_FOLDER)
createDirectory(FRAME_SAVE_FOLDER)
createDirectory(CONTOURS_SAVE_FOLDER)
createDirectory(FFT_SAVE_FOLDER)
createDirectory(HAVETEXT_SAVE_FOLDER)
createDirectory(ClEAN_SAVE_FOLDER)

#로컬 폴더에서 비디오에서 추출한 이미지를 관리하기 위한 딕셔너리 (id:link)
idlink_info = {}
idlength_info = {}


#필요한 리스트들
download_url_list = []
linklist = []

SEARCH_KEYWORD = input('검색어를 입력하세요 : ').replace(' ', '+')
PAGE_NUMGER = input('스크롤 횟수를 입력하세요 : ')

#webtooninfo 연결 수립
con = pymysql.connect(host='34.64.236.142', user='root', password='root',
                      db='webtooninfodb', charset='utf8mb4', autocommit=True)
cur = con.cursor()
print('구글 클라우드 DB 연결이 수립되었습니다. : '+str(con))
time.sleep(2)

#동영상 플랫폼 영상 수집
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
URL = "https://www.youtube.com/results?search_query=" + SEARCH_KEYWORD
driver.get(URL)
time.sleep(3)
scroll(PAGE_NUMGER)
html_source = driver.page_source
soup_source = BeautifulSoup(html_source, 'html.parser')
content_total = soup_source.find_all(class_ = 'yt-simple-endpoint style-scope ytd-video-renderer')
content_total_link = list(map(lambda data: "https://youtube.com" + data["href"], content_total))
print(str(SEARCH_KEYWORD) + '에 대한 영상 url을 저장하였습니다.')
print(content_total_link)
time.sleep(2)

#link 목록 저장
sql = "insert into links (link) (select link from WebtoonInfo);"
cur.execute(sql)
print(sql)

print('영상에 대한 정보를 db에 저장합니다.')
#영상 정보 db에 삽입
for contentlink in content_total_link :
    yt = YouTube(contentlink)

    id = contentlink[-5:]
    title = yt.title
    title = title.replace("'", "\\'")
    uploader = yt.author
    uploader = uploader.replace("'", "\\'")
    length = yt.length

    try :
        # 정보 저장용 sql문
        sql = "insert into WebtoonInfo (id, title, link, uploader, video_length, keyword) values ('{}', '{}', '{}', '{}', '{}', '{}')".format(
            id, title, contentlink, uploader, length, SEARCH_KEYWORD)
        print(str(contentlink)+' : id, title, link, uploader, video_length, keyword가 db에 저장되었습니다.')
        cur.execute(sql)
    except :
        pass


#작업에 필요한 컬럼을 다운로드. id컬럼과 link컬럼, video_length 컬럼 가져오기
bringinfo = "SELECT id, link, video_length FROM WebtoonInfo"
cur.execute(bringinfo)
idandlinkandlength = cur.fetchall()

#과거에 link를 가져와서 이미 다운로드 받은 영상은 다운로드 받지 않도록 함
pastlinkinfo = "SELECT link FROM links"
cur.execute(pastlinkinfo)
links = cur.fetchall()

print('동영상을 다운로드 합니다.')

#영상을 다운로드 하기 위해 필요한 정보들 각 저장
for bringid, bringlink, bringlength in idandlinkandlength :
    id = str(bringid)
    link = str(bringlink)
    length = int(bringlength)
    idlink_info[id] = link
    idlength_info[id] = length

for link in links :
    linklist.append(link[0])

#다운로드 link 확정
idlink_info = dict(map(reversed,idlink_info.items()))
for link in linklist :
    if (link in idlink_info.keys()) :
        del idlink_info[link]
idlink_info = dict(map(reversed,idlink_info.items()))

#비디오 다운로드
for downloadid, downloadlink in idlink_info.items() :
    yt = YouTube(downloadlink)
    try :
        yt.streams.filter(progressive=True, file_extension="mp4").first().download(output_path=VIDEO_DOWNLOAD_FOLDER,
                                                                                   filename=(downloadid + '.mp4'))
        print(str(downloadid) + ': 동영상을 다운로드 합니다.')
    except Exception as e:
        print(str(e) + ' : download를 실행하지 못 했습니다.')

print('동영상 다운로드가 끝났습니다.')
time.sleep(2)
print('프레임 추출을 시작합니다.')
time.sleep(2)
#비디오 길이에 따라 추출하는 frame의 수 조정
video_name_list, video_path_dict = getFilePathandName(VIDEO_DOWNLOAD_FOLDER) # file_name_list는 id list와 같다, 하지만 혹시 모르니까 폴더 내에서 검사

#비디오에서 프레임 추출
for id, length in idlength_info.items() :
    try :
        video_path = video_path_dict[id]
        count = 0
        video = cv2.VideoCapture(video_path)
        videoFrameCount = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

        if videoFrameCount < 35 :
            pass
        else :
            fps = int(video.get(cv2.CAP_PROP_FPS))
            if int(idlength_info[id]) < 30 :
                extractlength = 2
            else :
                extractlength = int(idlength_info[id] * 0.1)
            next_frame = fps * extractlength
            while (video.isOpened()):
                ret, frame = video.read()
                if (int(video.get(cv2.CAP_PROP_POS_FRAMES)) % (fps * extractlength) == 0):
                    savepath = FRAME_SAVE_FOLDER + id + '_%d.jpg' % count
                    cv2.imwrite(savepath, frame)
                    count += 1
                    next_frame += fps * extractlength
                    if next_frame > int(videoFrameCount):
                        break
            print(str(id) + ' 프레임을 추출하였습니다.')
            time.sleep(1)
    except Exception as e :
        print(str(e) + ' 이미 프레임 추출이 끝난 영상 입니다.')
        time.sleep(1)

print('전체 동영상에 대한 프레임 추출이 끝났습니다.')
time.sleep(2)
print('프레임에 대한 이미지 전처리 시작합니다.')

image_name_list, image_path_dict = getFilePathandName(FRAME_SAVE_FOLDER)

imagetogray = {}
imagetoCr = {}
imagetoCb = {}

for imageid in image_name_list :
    image = cv2.imread(image_path_dict[imageid], 1)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    Y, Cr, Cb = cv2.split(image)
    imagetogray[imageid] = Y
    imagetoCr[imageid] = Cr
    imagetoCb[imageid] = Cb


for imageid in image_name_list :
    contoursSavePath = CONTOURS_SAVE_FOLDER + imageid + '.jpg'
    cleanSavePath = ClEAN_SAVE_FOLDER + imageid + '.jpg'
    havetextSavePath = HAVETEXT_SAVE_FOLDER + imageid + '.jpg'

    image = cv2.imread(image_path_dict[imageid], 1)
    gray = imagetogray[imageid]

    cleanImage = ImageClear(gray)
    cv2.imwrite(cleanSavePath, cleanImage)

    ret2, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    binary = cv2.bitwise_not(binary)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for contour in range(len(contours)):
        cv2.drawContours(image, [contours[contour]], 0, (255, 0, 0), 3)
    rgb_count = cv2.inRange(image, (0, 0, 0), (255, 0, 0))
    cv2.imwrite(contoursSavePath, rgb_count)
    result = ocrtostr(cleanSavePath, 'kor+eng')
    if len(result) != 0 :
        shutil.copy(image_path_dict[imageid], havetextSavePath)
    else :
        pass

print('이미지 전처리가 끝났습니다.')

sql = "delete from links;"
cur.execute(sql)

print('db 연결을 해제합니다..')

con.commit()
con.close()
