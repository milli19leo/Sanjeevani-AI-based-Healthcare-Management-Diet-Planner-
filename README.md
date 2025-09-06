# Sanjeevani (AI-based Healthcare Management Diet Planner)

Sanjeevani is an intelligent, web-based healthcare management platform designed to simplify medical services for patients, healthcare providers, and administrators. It integrates intelligent tools like disease prediction, personalized diet planning, electronic health records (EHR), and doctor search to provide quick, reliable, and user-friendly health assistance.

# Features

● Electronic Health Records (EHR):
  Engineered a secure EHR module integrating Google Document AI (OCR) to digitize & analyze medical reports, with AES-256 encryption + role-based access control.
  
● Disease Prediction:
  Upload CBC reports (PDF or JPG), and the AI-powered engine will analyze key biomarkers and predict potential health risks using automated data extraction and ML models.

● Personalized Diet Plans:
  Users receive custom meal plans based on age, weight, health conditions, and goals. Meals are structured with appropriate nutrients and daily recommendations. This diet planner uses Random Forest ML, achieving ~85% prediction accuracy on curated health–nutrition datasets.

● Find a Specialist:
  Built a location-aware “Find Doctor” service with Google Maps API, improving doctor discovery efficiency by 60%.
  
  
# Tech Stack

 ● Frontend: HTML, CSS
 
 ● Backend: Python (Flask)
 
 ● Database: MySQL
 
 ● AI/ML Tools: Document AI, Cosine Similarity (for collaborative filtering)
 
 ● Hosting Protocol: HTTP/HTTPS
 
 ● Installation Guide

 For academic/demo purposes only.

  1. Clone the repository

         git clone https://github.com/your-repo/sanjeevani.git

  2. Install dependencies

         pip install -r requirements.txt

4. Configure the MySQL database and update credentials .

5. Run the app

         flask run
  
# UI Interfaces: image

● All Module
      
# Results

![Model Architecture](https://github.com/user-attachments/assets/2ddd0cd7-78ac-4dc0-bc10-1c82abf7b2a4)
![Training Pipeline](https://github.com/user-attachments/assets/fce0477f-de1b-477e-8ce4-ca74478a57e9)
![Generated Samples](https://github.com/user-attachments/assets/b6090b9c-884c-438f-966b-c525371cfaa6)
# Results

<img src="https://github.com/user-attachments/assets/2ddd0cd7-78ac-4dc0-bc10-1c82abf7b2a4" width="600"/>
<img src="https://github.com/user-attachments/assets/fce0477f-de1b-477e-8ce4-ca74478a57e9" width="600"/>
<img src="https://github.com/user-attachments/assets/b6090b9c-884c-438f-966b-c525371cfaa6" width="600"/>
# Comparison

<p float="left">
  <img src="https://github.com/user-attachments/assets/2ddd0cd7-78ac-4dc0-bc10-1c82abf7b2a4" width="400"/>
  <img src="https://github.com/user-attachments/assets/fce0477f-de1b-477e-8ce4-ca74478a57e9" width="400"/>
</p>

