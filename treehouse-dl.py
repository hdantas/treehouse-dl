import os
import sys

from bs4 import BeautifulSoup
import requests
import configparser

class Library:
    def __init__(self, session, library_url, base_url):
        
        self.url = library_url
        self.session = session
        self.BASE_URL = base_url

        self.library_session = session.get(self.url)
        self.library_bs4 = BeautifulSoup(self.library_session.text)

        self.topics = []
        self.select_topics = []

    def _retrieve_all_topics(self):
        topics = self.library_bs4.select('ul#library-topic-filters > li')
        for topic in topics:
            topic_name = topic.select('span')[0].text.strip()
            topic_url = self.BASE_URL + topic.select('a')[0]['href']
            self.add_topic(Topic(topic_url, self.session, self.BASE_URL))

    def get_all_topics(self):
        if len(self.topics) < 1:
            self._retrieve_all_topics()
        return self.topics

    def add_topic(self, topic):
        if isinstance(topic, Topic) and topic not in self.topics:
            self.topics.append(topic)

    def download_all_videos(self, filepath = ""):
        for topic in self.get_all_topics():
            topic.download_all_videos(filepath)

    def download_all_topic_videos(self, topic_index, filepath=""):
        self.get_all_topics()[topic_index].download_all_videos(filepath)

    def choose_topics_to_download(self):
        all_topics_names = [topic.name for topic in self.get_all_topics()]
        topics_list = '\n'.join(['[' + str(key + 1) + '] - ' + name for key, name in enumerate(all_topics_names)])
        print('\nAvailable topics:\n' + topics_list + \
            '\n\nSpecify the numbers of topics through space (like this 1 3 6)\n')
        
        
        self.select_topics = list(map(int, input('Enter numbers:').split(' ')))
        print('You chose: ' + ', '.join([all_topics_names[i - 1] for i in self.select_topics]))

    def download_chosen_topics(self, filepath = ""):
        all_topics_names = [topic.name for topic in self.get_all_topics()]
        for i in self.select_topics:
            print ("Downloading " + all_topics_names[i - 1] + ". Please wait ...")
            self.download_all_topic_videos(i - 1, filepath)

class Topic:
    def __init__(self, topic_url, session, base_url):
        
        self.url = topic_url
        self.session = session
        self.BASE_URL = base_url

        self.topic_session = session.get(self.url)
        self.topic_bs4 = BeautifulSoup(self.topic_session.text)
        self.name = self.topic_bs4.select(".topic-heading h1")[0].text.strip()

        self.parts = [] #a part can be a course or a workshop


    def _retrieve_all_parts(self):
    #find all courses and workshops that belong to this topic and add to courses and workshops array
        topic_parts = self.topic_bs4.select('li.card')

        for index, part in enumerate(topic_parts):
            new_part_url = self.BASE_URL + part.select('a.title')[0]['href']
            part_type = part.find('strong').text
            
            if part_type == "Workshop":
                self.add_part(Video(index, new_part_url, self.session, self.BASE_URL))
            elif part_type == "Course":
                self.add_part(Course(index, new_part_url, self.session, self.BASE_URL))

    def get_all_parts(self):
        if len(self.parts) < 1:
            self._retrieve_all_parts()
        return self.parts

    def add_part(self, part):
        if (isinstance(part, Course) or isinstance(part, Video)) and part not in self.parts:
            self.parts.append(part)

    def download_all_videos(self, filepath = ""):
        for part in self.get_all_parts():
            
            if isinstance(part, Course):
                new_filepath = os.path.join(filepath, self.name)
                part.download_all_videos(new_filepath, True)

            elif isinstance(part, Video):
                new_filepath = os.path.join(filepath, self.name, str(part.index + 1) + '_' + part.name)
                part.download_video(new_filepath, False)

class Course:
    def __init__(self, index, course_url, session, base_url):
        
        self.index = index
        self.url = course_url
        self.session = session
        self.BASE_URL = base_url

        self.course_session = session.get(self.url)
        self.course_bs4 = BeautifulSoup(self.course_session.text)

        self.name = self.course_bs4.select('.hero-meta h1')[0].text.strip() if self.course_bs4.select('.hero-meta') else ''
        self.level = self.course_bs4.select('.hero-meta span')[0].text.strip() if self.course_bs4.select('.hero-meta') else ''
        self.sections = []
        

    def _retrieve_all_sections(self):
    #find all sections that belong to this course and add to sections array
        course_sections = self.course_bs4.find_all('div', {'class': 'contained featurette',
                                               'data-featurette': 'expandable-content-card'})
    
        for section_index, section in enumerate(course_sections):
            new_section_title = section.select('.achievement-meta a')[0].text
            new_section = Section(section_index, section, self.session, self.BASE_URL)
            self.add_section(new_section)

    def get_all_sections(self):
        if (len(self.sections) < 1):
            self._retrieve_all_sections()
        return self.sections

    def add_section(self, section):
        if isinstance(section, Section) and section not in self.sections:
            self.sections.append(section)

    def download_all_videos(self, filepath, index_in_filename=True):
        for section in self.get_all_sections():
            new_filepath = os.path.join(filepath, str(self.index + 1) + "_" + self.name)
            section.download_all_videos(new_filepath, index_in_filename)

class Section:
    def __init__(self, index, section_bs4, session, base_url):
        
        self.index = index
        self.section_bs4 = section_bs4
        self.session = session
        self.BASE_URL = base_url
        self.name = self.section_bs4.select(".achievement-meta")[0].h2.a.text.strip() \
            if self.section_bs4.select('.achievement-meta') else ''
        self.videos = []

    def _retrieve_all_videos(self):

        section_videos = self.section_bs4.select('.icon.icon-video')

        for video_index, video in enumerate(section_videos):
            new_video_url = self.BASE_URL + video.find_parent('a')['href']

            new_video = Video(video_index, new_video_url, self.session, self.BASE_URL)
            self.add_video(new_video)

    def get_all_videos(self):
        if (len(self.videos) < 1):
            self._retrieve_all_videos()
        return self.videos

    def add_video(self, video):
        if isinstance(video, Video) and video not in self.videos:
            self.videos.append(video)

    def download_all_videos(self, filepath, index_in_filename=True):
        for video in self.get_all_videos():
            new_filepath = os.path.join(filepath, str(self.index + 1) + "_" + self.name)
            video.download_video(new_filepath, index_in_filename)

class Video:
    def __init__(self, index, video_url, session, base_url):
        
        self.index = index
        self.url = video_url
        self.session = session
        self.BASE_URL = base_url

        self.video_session = session.get(self.url)
        self.video_bs4 = BeautifulSoup(self.video_session.text)

        video_meta = self.video_bs4.select('#video-meta')[0]
        self.name = video_meta.h1.text.strip()
        self.duration = video_meta.span.text        
        self.description = video_meta.p.text

        self.download_links = {'files': "", 'hd': "", 'sd': "", 'srt': ""}


    def _retrieve_download_links(self):
        links = self.video_bs4.select('#downloads-tab-content')[0].select('a')
        for link in links:
            title = link.strong.text

            if title.find('Project Files') != -1:
                self.download_links['files'] = link['href']
            
            if title.find('High Definition Video') != -1:
                self.download_links['hd'] = self.BASE_URL + link['href']
            
            if (title.find('Standard Definition Video') != -1):
                self.download_links['sd'] = self.BASE_URL + link['href']
            
            if title.find('Video Transcript') != -1:
                self.download_links['srt'] = link['href']

    def get_all_download_links(self):
        if (self.download_links['sd'] == "" or self.download_links['hd'] == ""):
            self._retrieve_download_links()
        return self.download_links

    def download_video(self, filepath, index_in_filename=True):
        #ensure _retrieve_download_links is called when needed
        download_links = self.get_all_download_links()

        if(download_links['hd'] != ""):
            video_url = download_links['hd']
        else:
            video_url = download_links['sd']

        name_prefix = str(self.index + 1) + '_' if index_in_filename else ''
        filename = name_prefix + self.name

        self._download_file(video_url, filepath, filename + '.mp4')

        if(download_links['srt'] != ""):
            self._download_file(download_links['srt'], filepath, filename + '.srt')

        if(download_links['files'] != ""):
            self._download_file(download_links['files'], filepath, filename + '.zip')


    def _download_file(self, url, path, name):
    # Create and fill file based on the URL, overwrites existing file
    # If the file does not exist it will create it as well as the path to reach it
        print("Downloading file from URL:", url)
        if not os.path.exists(path):
            os.makedirs(path)

        filename = os.path.join(path, name)
                
        if not os.path.isfile(filename):
            r = self.session.get(url, stream=True)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=2048):
                    if chunk:
                        f.write(chunk)
                        f.flush()
            r.close()
            message = config["message"]["success"]
        else:
            message = config["message"]["exists"]

        print(message.format('File', filename))



def do_auth(user, pwd): #login using user and pwd, returns logged in session
    sess = requests.Session()

    login_page = sess.get('https://teamtreehouse.com/signin')
    login_page_soup = BeautifulSoup(login_page.text)
    
    token_val = login_page_soup.find('input', {'name': 'authenticity_token'}).get('value')
    utf_val = login_page_soup.find('input', {'name': 'utf8'}).get('value')
    
    post_data = {'user_session[email]': user, 'user_session[password]': pwd, 'utf8': utf_val,
                 'authenticity_token': token_val}

    profile_page = sess.post('https://teamtreehouse.com/person_session', data=post_data)
    
    profile_page_soup = BeautifulSoup(profile_page.text)
    auth_sign = profile_page_soup.title.text
    if auth_sign:
        if auth_sign.lower().find('home') != -1:
            print('Login successful!')
        else:
            print('Not found login attribute\nExit...')
            sys.exit(0)
    else:
        raise Exception('Login failed!')

    return sess



if __name__ == '__main__':
    config = configparser.ConfigParser(interpolation=None)
    config.read('config.conf')

    _user = config['auth']['user']
    _pass = config['auth']['password']
    path = config['auth']['path']

    my_library_url = config['url']['library_url']
    my_base_url = config['url']['base_url']
    sess = do_auth(_user, _pass)
    print("Fetching available topics, please wait ...")
    library = Library(sess, my_library_url, my_base_url)
    library.choose_topics_to_download()
    
    done = False
    while not done:
        try:        
            library.download_chosen_topics(path)
            done = True
        except Exception as e:
            print("Error while downloading! Trying again")
            print(e)
            #Close session and create new one on error
            sess.close()
            library.session = do_auth(_user, _pass)

    print("Bye...")

