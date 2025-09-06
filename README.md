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
![image](https://github.com/user-attachments/assets/33ff3099-d5f3-4674-88a8-4332a49c0070)
![image](https://github.com/user-attachments/assets/546b9e6a-37fa-4db9-8e70-b01ff196871e)
![image](https://github.com/user-attachments/assets/5614c8c7-a3ba-4851-bde2-a86f41165f2c)
![image](https://github.com/user-attachments/assets/36ea8843-a75e-4fe2-be0d-3c9f94057507)



