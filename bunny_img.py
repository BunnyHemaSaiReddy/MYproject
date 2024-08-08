import pywhatkit.whats
import streamlit as st
import streamlit_option_menu 
import random
import mysql.connector 
import base64
import boto3
import json
import os  
import datetime
import smtplib
import time
import requests
import io
import bunny_key
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import google.generativeai as genai
import speech_recognition as sr
import gtts
import googlesearch
import bunny_lang
import pywhatkit
import asyncio
import face_recog
import PIL.Image as PIL


class sql_:
    def __init__(self):
        self.con = mysql.connector.connect(
            host='localhost',
            user='root',
            passwd='bunny',
            auth_plugin='mysql_native_password'
        )
        self.cursor=self.con.cursor()
    def verify_mail(self):
        pass
    def is_database(self,data):
        self.cursor.execute("show databases;")
        #st.write(self.cursor.fetchall())
        databases = [db[0] for db in self.cursor.fetchall()]
        #st.write(databases)
        return data in databases
    def create_database(self,mail):
        mail=mail.split('@')[0]
        if not self.is_database(mail):
            st.success('your mail reggestred sucessfully')
            passwd1=st.text_input("Enter password",type='password')
            passwd2=st.text_input("Reenter password",type='password')
            if passwd1==passwd2 and passwd1 and passwd2:
                self.cursor.execute(f"create database {mail};")
                self.cursor.execute(f"use {mail};")
                self.cursor.execute("create table  password (passwd varchar(10));")
                self.cursor.execute("commit;")
                self.cursor.execute("insert into password values('{}');".format(passwd1))
                self.cursor.execute('commit;')
                self.cursor.execute("create table  store_img (input_prompt varchar(150),output_img longtext);")
                self.cursor.execute("commit;")
                self.cursor.execute("create table  store_chat (input varchar(500),output longtext);")
                self.cursor.execute("commit;")
                self.cursor.execute("create table  img_img (input_prompt varchar(500),input_image longtext,output longtext);")
                self.cursor.execute("commit;")
                self.cursor.execute("create table  img_text (input_prompt varchar(500),input_image longtext,output longtext);")
                self.cursor.execute("commit;")
                return 1
            elif passwd1 and passwd2:
                st.warning("check whather both passwords are same")
                return 0
        else:
            st.warning("Already, your mail logged, please go to login section")
            return 0
sql=sql_()

def mail(e,otp):
    sender_email = bunny_key.app_email
    sender_password = bunny_key.app_pass
    receiver_email = e
    subject = "otp verification"
    message = (
        "This message is from Bunny chatbot. To verify your account is valid or not, "
        "this is the 6-digit code that you need to enter to verify:\n"
        f"{otp}"
        "\nEnter the OTP in the portal."
    )
    html_message = message.replace('\n', '<br>').replace(str(otp), f'<span style="color: red; font-weight: bold;">{otp}</span>')
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(html_message, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return f"OTP is send to the mail  {e}"
    except Exception as e:
        return f"Failed to send email. Error: {e}\n Try again"


def login():
    with st.sidebar as _:
        s=st.select_slider('Choose the following options to Login:',['Login','Signin'])
    if s=='Login':
        st.header('Login')
        #st.markdown('![Enter your mail for sign in](https://static.vecteezy.com/system/resources/previews/000/324/973/original/vector-email-icon.jpg)')
        email=st.text_input("Enter your mail 📧").replace('.','')
        if email:
            if sql.is_database(email.split('@')[0]):
                sql.cursor.execute(f"use {email.split('@')[0]};")
                sql.cursor.execute("commit;")
                sql.cursor.execute("select * from password;")
                passwd=st.text_input("Enter your password",type='password')
                if passwd:
                    if passwd==sql.cursor.fetchall()[0][0]:
                        st.session_state.logged_in = True
                        st.session_state.email= email
                        return 1
                    else:
                        st.warning("Enter the correct password")
                        return 0
            else:
                st.warning("Your database not found please signin")
                return 0
    if s=='Signin':
        st.header('Sign in')
        email_=st.text_input("Enter signin mail 📧")
        #rand_int=random.randint(100000,999999)
        if email_:
            if 'rand_int' not in st.session_state:
                st.session_state.rand_int = random.randint(100000, 999999)
            rand_int = st.session_state.rand_int
            st.write(mail(email_,rand_int))
            otp=st.text_input(label='Enter OTP',placeholder='000000').replace(' ','')
            if otp==str(rand_int):
                if sql.create_database(email_.replace('.','')):
                    st.session_state.logged_in = True
                    st.session_state.email= email_
                    return 1
            else:
                return 0

def generate_image(prompt, width=512, height=512, number_of_images=3,cfg_scale=10, seed=10):
    os.environ['AWS_ACCESS_KEY_ID'] = bunny_key.access_id   
    os.environ['AWS_SECRET_ACCESS_KEY'] = bunny_key.api_key
    # os.environ['AWS_SESSION_TOKEN'] = 'YOUR_SESSION_TOKEN' 
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'  

    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    model_id = "amazon.titan-image-generator-v1"
    native_request = {
        "textToImageParams": {
            "text": prompt
        },
        "taskType": "TEXT_IMAGE",
        "imageGenerationConfig": {
            "cfgScale": cfg_scale,
            "seed": seed,
            "width": width,
            "height": height,
            "numberOfImages": number_of_images
        }
    } 
    request = json.dumps(native_request)
    async def genmsg():
        return client.invoke_model(modelId=model_id, body=request)
    async def spin():
        with st.spinner("Generating..."):
            await asyncio.sleep(10)
    async def main():
        result, _ = await asyncio.gather(genmsg(), spin())
        return result
    response = asyncio.run(main())
    model_response = json.loads(response["body"].read())
    l=[]
    for _ in range(len(model_response["images"])):
        base64_image_data = model_response["images"][_]
        image_data = base64.b64decode(base64_image_data)
        l.append(image_data)
    st.markdown("### :rainbow[The images for the prompt]🔥")
    col= st.columns(len(model_response["images"]))
    j=1
    for i in col:
        with i:
         st.image(l[j-1], caption=f"Image {j}", use_column_width=True)
        j+=1
  
def text_to_text():
    api='AIzaSyCBHTmgKXbiputUhfU9PlFUufQYVGqsMHs'
    genai.configure(api_key=api)
    model = genai.GenerativeModel('gemini-pro') 
    st.markdown('## :red[Input type:]')
    chat_c=st.radio("",("Text📄","Speak🎤"))
    dict_lang=bunny_lang.lang()
    choice_trans=st.selectbox("Select the language for output:",["DEFAULT-English"]+list(dict_lang.keys()))
    to='en'
    input_text=""
    if choice_trans!="DEFAULT-English":
        to=dict_lang[choice_trans]
    if chat_c=="Text📄":
        st.session_state[input_text]=""
        input_text=st.text_area('**🤖**',key="input_text",placeholder='Enter the prompt.....',disabled=False)
        
    elif chat_c=='Speak🎤':
        st.markdown("### :violet[Speak now:] 🗣️ ")
        input_text=st.text_area('**🤖**',value=speak(),disabled=False)
    if st.button("Generate:") and input_text:
        for i in range(1):
            if st.button("cancel"):
                break
            async def genmsg():
                return model.generate_content(input_text)
            async def spin():
                with st.spinner("Generating..."):
                    await asyncio.sleep(2)
            async def main():
                result, _ = await asyncio.gather(genmsg(), spin())
                return result
            result = asyncio.run(main())
            if result:
                for i in result:
                    output=i.text
                output=bunny_lang.trans(output,to)
                if 0 and st.button("Send whatshapp") :
                    ph_no=st.text_input(label="Enter the Phone number:",placeholder=0000000000)
                    if len(ph_no)==10:
                        pywhatkit.whats.sendwhatmsg_instantly("+91"+ph_no,output)
                def generate():
                    for i in output:
                        yield i
                        time.sleep(0.02)
                st.write_stream(generate)
                st.header("Relevant video link")
                st.write(pywhatkit.playonyt(input_text,open_video=False))
                try:
                    st.markdown("### :red[Links that provide extra content for your text :]")
                    query=input_text
                    g_s=googlesearch.search(query,num_results=5)
                    for j in g_s:
                        st.write(j)
                except Exception as e:
                    j=str(e)[45:]
                    st.warning(j)
                try:
                    sound_text=gtts.gTTS(output,lang=to)
                    audio_buffer = io.BytesIO()
                    sound_text.write_to_fp(audio_buffer)
                    audio_buffer.seek(0)                    
                    st.audio(audio_buffer,format="audio/mp3")
                except Exception:
                    pass
                if st.button("New attempt"):
                    st.session_state[input_text]=""
                    st.rerun()
    
def imganalysis():
    flag=0
    api='AIzaSyCBHTmgKXbiputUhfU9PlFUufQYVGqsMHs'
    genai.configure(api_key=api)
    img_model=genai.GenerativeModel('gemini-1.5-flash')
    with st.sidebar:
        img__ = st.select_slider("Choose an option:", ["Camera","Device","URL"],value="Device")
    if img__=="Device":
      img_name=st.file_uploader("Upload the file from the computer:")
      if img_name:
        img=PIL.open(img_name)
        flag=1
    if img__=="Camera" :
        __='''st.markdown("### :rainbow[Press space bar to capture an image]")
        if 'img' not in st.session_state:
            img=face_recog.face()
            st.session_state.img=img
        elif 'img' in st.session_state:
            img=st.session_state.img '''   
        img=st.camera_input("Enter the camera input :")
        img=PIL.open(img)
        if img:
            flag=1
    if img__=='URL':
        st.markdown("### :rainbow[Make sure that you providing the correct URL]")
        input_url=st.text_input("Enter the URL :")
        if input_url:
            try:
                req = requests.get(input_url)
                byte = io.BytesIO(req.content)
                st.write(byte)
                img = PIL.open(byte)
            except Exception as e:
                st.warning("provide the correct URl - Hint : check wheather link ending with jpg or png and starting with http//.www")
            flag=1
    if flag:
        col,_=st.columns(2)
        with col:
            st.image(img,use_column_width=True)
        if st.button("New attempt"):
            del st.session_state.img
            st.experimental_rerun()
        chat_c=st.radio("",("Text📄","Speak🎤"))
        st.session_state.img_input = ""
        if chat_c=="Text📄":
            st.session_state.img_input=st.text_input('**🤖**',placeholder='Enter the prompt.....',disabled=False)
        elif chat_c=='Speak🎤':
            st.markdown("### :violet[Speak now:] 🗣️ ")
            st.session_state.img_input=st.text_input('**🤖**',value=speak(),disabled=False)
        if st.session_state.img_input:
            async def genmsg():
                return img_model.generate_content([st.session_state.img_input,img])
            async def spin():
                with st.spinner("Generating..."):
                    await asyncio.sleep(3)
            async def main():
                result, _ = await asyncio.gather(genmsg(), spin())
                return result
            result = asyncio.run(main())
            def generate():
                    for i in result.text:
                        yield i
                        time.sleep(0.02)
            st.write_stream(generate)
            
                
def update_image(image , prompt ,n):
    os.environ['AWS_ACCESS_KEY_ID'] = bunny_key.access_id
    os.environ['AWS_SECRET_ACCESS_KEY'] = bunny_key.api_key
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    model_id = "amazon.titan-image-generator-v1"
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    input_image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
    native_request = {
        "imageVariationParams": {
            "images": [input_image_data],
            "text": prompt
        },
        "taskType": "IMAGE_VARIATION",
        "imageGenerationConfig": {
            "cfgScale": 8,
            "seed": 0,
            "width": 1024,
            "height": 1024,
            "numberOfImages": n
        }
    }
    request = json.dumps(native_request)

    try:
        async def genmsg():
            return client.invoke_model(modelId=model_id, body=request)
        async def spin():
            with st.spinner("Generating..."):
                await asyncio.sleep(6)
        async def main():
            result, _ = await asyncio.gather(spin(),genmsg())
            return result
        response = asyncio.run(main())
        response_body = response['body'].read().decode('utf-8')
        model_response = json.loads(response_body)
        
        images = model_response.get("images", [])
        if not images:
            raise ValueError("No images found in the response.")
        l=[]
        for  base64_image_data in images:
            image_data = base64.b64decode(base64_image_data)
            l.append(image_data)
        st.markdown("### :rainbow[The images for the prompt]🔥")
        col= st.columns(len(model_response["images"]))
        j=1
        for i in col:
            with i:
                st.image(l[j-1], caption=f"Image {j}", use_column_width=True)
                j+=1
        if st.button("New attempt"):
            st.rerun()   
    except Exception as e:
        st.warning(f"An error occurred: {e}")

                   
def speak():
    rec=sr.Recognizer()
    with sr.Microphone() as mic:
        sound=rec.listen(mic)
        text_rec=rec.recognize_google(sound)
        return text_rec
 
async def show_time():
    time_placeholder = st.empty()
    start_time = time.time()
    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time
        time_placeholder.text(f"Elapsed time: {elapsed_time:.2f} seconds")
        await asyncio.sleep(0.1)

if __name__=='__main__':          
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        with st.sidebar as s:   
            st.title(":blue[User] :sunglasses: :")
            st.header(f":red[{st.session_state.email.split('@')[0]}]",divider="rainbow")
            s=streamlit_option_menu.option_menu(None,['Home','TEXT TO TEXT','TEXT TO IMAGE','IMAGE TO TEXT','EDIT IMAGE','PDF ANALYSIS'],icons=['house','chat','images','images','card-image','folder'])
        if s=='TEXT TO IMAGE':
            st.markdown(f'<span style="font-size: 25px;">🕗</span> {datetime.datetime.today().hour}:{datetime.datetime.today().minute}:{datetime.datetime.today().second}', unsafe_allow_html=True)
            size=st.selectbox("Enter the size image :",['256x256','512x512','1024x1024','2048x2048'],index=2)
            number_images=st.slider("Select the number of images :",min_value=1,max_value=5)
            prompt=st.text_input('Enter a prompt')
            if size:
                width=size.split('x')[0]
                height=size.split('x')[1]
            if prompt and width and height:
                generate_image(prompt=prompt,width=int(width),height=int(height),number_of_images=int(number_images))
        if s=='TEXT TO TEXT':
            text_to_text() 
        if s=="IMAGE TO TEXT":
            imganalysis()   
        if s=='EDIT IMAGE':
            img_name=st.file_uploader("Upload the file from the MY-PC:")
            if img_name:
                img=PIL.open(img_name)
                cols,_=st.columns(2)
                with cols:
                    st.image(img)
                no_image=st.slider("Enter the number of images you want",1,5)
                input_prompt=st.text_input("**:blue[Enter the changes you want to do for Images:]**")
                if st.button("Generate"):
                    update_image(img,input_prompt,no_image)
            else:
                st.warning("Upload a pic with less than 25MB \n **Try to provide a photo of non Human**")
    else:
        if login():
            st.success("Sucessfully logged in")
            with st.spinner() as _:
                time.sleep(2)
            st.balloons()
            time.sleep(1.5)
            st.rerun()
            