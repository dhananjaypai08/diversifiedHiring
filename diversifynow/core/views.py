from django.shortcuts import render, redirect
import csv
import os
import pandas as pd
import plotly.express as px 
from plotly.offline import plot
from pandasai import PandasAI
from api.models import User
from api.serializers import UserSerializer
from hashlib import sha256
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from core.settings import EMAIL_HOST_USER
import random


def index(request):
    if request.session.get('user_id'):
        return redirect(home)
    msg = {}
    msg["title"] = "Login"
    msg["status"] = 1
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        hash = sha256(password.encode()).hexdigest()
        users = User.objects.filter(email=email)
        flg = 0
        for user in users:
            if user.password == hash:
                otp = str(random.randrange(1000,99999))
                otp_hash = str(sha256(otp.encode()).hexdigest())
                request.session['on_hold'] = user.id
                user.data = otp_hash
                user.save()
                flg = 1
                break
        if flg == 1:
            try:
                subject = "One-Time Password to Login to Your DiversifyNow Account"
                message = f"Hello {user.username} \n Your Verification OTP is : {otp}. \n Please use the OTP code to complete your login request.\n\n\n Best Regards,\nDiversifyNow"
                send_mail(subject, message, EMAIL_HOST_USER, [user.email], fail_silently=True)
                return redirect(email_verify)
            except:
                msg['status'] = 0
        else: msg['status'] = -1

    return render(request, 'login.html', msg)


def email_verify(request):
    if not request.session.get('on_hold'): return redirect(index)
    if request.session.get('user_id'): return redirect(home)
    user = User.objects.get(id=request.session['on_hold'])
    user_data = UserSerializer(user)
    msg = {}
    msg['username'] = user_data['username'].value
    msg['status'] = 1
    msg['title'] = 'Login'
    if request.method == 'POST':
        otp = str(request.POST.get('otp'))
        hash = str(sha256(otp.encode()).hexdigest())
        if user_data['data'].value == hash:
            del request.session['on_hold']
            request.session['user_id'] = user_data['id'].value
            print(request.session.get('on_hold'), request.session.get('user_id'))
            return redirect(index)
        msg['status'] = -1

    return render(request, 'emailverify.html', msg)
        

def register(request):
    if request.session.get('user_id'):
        return redirect(home)
    msg = {}
    msg["title"] = "Register"
    if request.method == 'POST':
        username, email, password = request.POST.get('username'), request.POST.get('email'), request.POST.get('password')
        hash = sha256(str(password).encode()).hexdigest()
        user = User(username=username, email=email, password=hash, data='')
        user.save()
        msg['status'] = 1
    return render(request, 'register.html', msg)


def logout(request):
    if request.session.get('user_id'):
        del request.session['user_id']
    return redirect(index)


def home(request):
    if not request.session.get('user_id'):
        return redirect(index)
    msg = {}
    msg["title"] = "Dashboard"
    return render(request, 'home.html',msg)


def historic(request):
    if not request.session.get('user_id'): return redirect(index)
    msg = {"title": "Dashboard", "description": "This is the landing Page"}
    data = []
    with open('static/MOCK_DATA.csv', mode='r') as file:
        csvfile = csv.reader(file)
        for ind, lines in enumerate(csvfile):
            if ind != 0:
                inddata = {
                    "Name": lines[1],
                    "Hired": lines[2],
                    "Previous CTC": lines[3],
                    "Gender": lines[4],
                    "Experience": lines[5]
                }
                data.append(inddata)

    #print(data)
    df = pd.DataFrame(data)
    # Calculate Gender Ratio
    gender_counts = df['Gender'].value_counts()
    gender_ratio = gender_counts / gender_counts.sum()
    msg["gender_ratio"] = gender_ratio 
    # Analyze Hired vs. Not Hired
    hired_gender_counts = df[df['Hired'] == True]['Gender'].value_counts()
    not_hired_gender_counts = df[df['Hired'] == False]['Gender'].value_counts()
    #Gender Distribution for Hired Candidates:
    msg["hired_counts"] = hired_gender_counts
    #Gender Distribution for Not Hired Candidates:
    msg["unhired_counts"] = not_hired_gender_counts
    # Mean Previous Compensation by gender
    mean_previous_ctc = df.groupby('Gender')['Previous CTC'].mean()
    msg["mean_previous_ctc"] = mean_previous_ctc
    # Experience Levels distribution by gender
    experience_gender_counts = df.groupby('Gender')['Experience'].value_counts()
    msg["experience_gender_counts"] = experience_gender_counts
    #summary stats
    msg["summary_stats"] = df.describe()
    
    fig_bar = px.bar(
        df.loc[1:50], x="Gender", y=["Previous CTC", "Experience", "Hired"], title="Bar Graph", height=500, hover_data=["Name"]
    )
    fig_scatter = px.scatter(
        df, x="Experience", y="Previous CTC", color="Gender", height=500, hover_data=["Name"], title="Scatter Plot"
    )
    fig_pie = px.pie(
        df.loc[1:30], values="Experience", names="Gender", height=250, title="Pie Chart"
    )
    
    bar_plot = fig_bar.to_html(full_html=False, include_plotlyjs=False)
    scatter_plot = fig_scatter.to_html(full_html=True, include_plotlyjs=False)
    pie_plot = fig_pie.to_html(full_html=False, include_plotlyjs=False)
    msg["barplot"] = bar_plot
    msg["scatterplot"] = scatter_plot
    msg["pieplot"] = pie_plot
    
    return render(request, 'historical.html', msg)


def prompt(request):
    if not request.session.get('user_id'): return redirect(index)
    msg = {}
    prompt = None
    msg["prompt"] = prompt
    imported_data = None
    if request.method == 'POST':
        button = False
        prompt = request.POST.get('prompt')
        
        csv_file = request.FILES.get('data')
        
        if csv_file:
            imported_data = pd.read_csv(csv_file)
            imported_data.to_csv('media/data.csv')
            #print(imported_data.describe())
            # imported_data = pd.DataFrame({
            # "country": ["United States", "United Kingdom", "France", "Germany", "Italy", "Spain", "Canada", "Australia", "Japan", "China"],
            # "gdp": [19294482071552, 2891615567872, 2411255037952, 3435817336832, 1745433788416, 1181205135360, 1607402389504, 1490967855104, 4380756541440, 14631844184064],
            # "happiness_index": [6.94, 7.16, 6.66, 7.07, 6.38, 6.4, 7.23, 7.22, 5.87, 5.12]
            # })
            button = True
        
        if prompt:
            imported_data = pd.read_csv('media/data.csv')
            from pandasai.llm.openai import OpenAI
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.getenv('api_key')
            llm = OpenAI(api_token=api_key)
            pandas_ai = PandasAI(llm)
            response = pandas_ai.run(imported_data, prompt=prompt)
            print(response, type(response))
            msg["prompt"] = response
        msg['button'] = button
        msg["imported_data"] = imported_data.loc[0:9]
    return render(request, 'prompt.html', msg)


def custom(request):
    msg = {}
    import_form = True
    changed = False
    if request.method == 'POST':
        csv_file = request.FILES.get('data')
        num_rows = request.POST.get('num_rows')
        imported_data = None
        button = False
        edit = False
        if csv_file:
            imported_data = pd.read_csv(csv_file)
            imported_data.to_csv('media/custom.csv')
            button = True
        elif num_rows:
            num_rows = int(num_rows)
            df = pd.read_csv('media/custom.csv')
            columns = list(df.columns)
            columns.pop(0)
            num_columns = len(columns)
            # data = [request.POST.getlist(f'data[{i}]') for i in range(num_rows)]
            data = []
            for i in range(num_rows):
                lst = request.POST.getlist(f'data[{i}]')
                lst.pop(0)
                data.append(lst)
            imported_data = pd.DataFrame(data, columns=columns)
            imported_data.to_csv('media/custom.csv')
            changed=True
            button=True
        else:
            imported_data = pd.read_csv('media/custom.csv')
            edit = True
            import_form = False
        msg['imported_data'] = imported_data   
        msg['button'] = button
        msg['edit'] = edit
        msg['changed'] = changed
    msg['import_form'] = import_form      
    return render(request, 'custom.html', msg)