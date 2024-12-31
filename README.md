Fireside Chat

Description

Fireside Chat is an experimental application showcasing the recent advancements in natural language processing and conversational AI. It integrates cutting-edge AI models, real-time text-to-speech synthesis, and voice-driven interactions to create an immersive debate experience.

As the author, I believe this project demonstrates how AI can bridge the gap between human conversations and machine intelligence. With potential for further development, this work can be extended to create tools for education, collaborative brainstorming, and virtual assistants. I invite contributors to help shape this project into a fully open-source AI tool that benefits the community.

Features
	•	Voice-Driven Interactions: Moderators can set debate topics using voice input.
	•	Dynamic AI Personas: Each persona is equipped with unique traits, conversational styles, and voices.
	•	Real-Time Responses: Responses are spoken aloud using realistic text-to-speech synthesis.
	•	Live Transcript Updates: Monitor all conversations in real-time through a detailed transcript.
	•	Customizable Personas: Easily define new personas with distinct system prompts and voices.
	•	Spinner Feedback: Indicates active processing for smooth user experience.

Installation

Prerequisites
	•	Node.js: For frontend development.
	•	Python 3.8+: For backend API development.
	•	macOS or other OS with speech synthesis support.

Step 1: Clone the Repository

git clone https://github.com/your-repo/fireside-chat.git
cd fireside-chat

Step 2: Backend Setup
	1.	Navigate to the backend folder:

cd backend


	2.	Create a Python virtual environment:

python3 -m venv venv
source venv/bin/activate


	3.	Install dependencies:

pip install -r requirements.txt


	4.	Start the backend server:

uvicorn main:app --reload



Step 3: Frontend Setup
	1.	Navigate to the frontend folder:

cd ../frontend


	2.	Install dependencies:

npm install


	3.	Start the development server:

npm start

Upgrading to Latest Version
	1.	Pull the latest changes from the repository:

git pull origin main


	2.	Update backend dependencies:

cd backend
pip install -r requirements.txt --upgrade


	3.	Update frontend dependencies:

cd ../frontend
npm install

Contributing

This project thrives on collaboration! Here’s how you can contribute:
	•	Enhance AI Personas: Add new personas with unique styles and voices.
	•	Refine AI Models: Experiment with better AI models for more engaging responses.
	•	Build New Features: Suggest and implement new functionalities.
	•	Fix Bugs: Identify and resolve issues in both backend and frontend.
	•	Documentation: Improve project documentation to make it beginner-friendly.

Join us in building more open-source AI tools for the community! Submit pull requests or open issues in the repository.

To-Do
	•	Implement CI/CD for seamless deployment.
	•	Add internationalization support for global accessibility.
	•	Enable cross-platform text-to-speech functionality.
	•	Enhance scalability for larger user bases.
	•	Build comprehensive unit and integration tests.

License

This project is licensed under the MIT License, making it free and open-source for the community.

Requirements
	•	Operating System: macOS (preferred) or other OS with TTS support.
	•	Frontend: ReactJS.
	•	Backend: FastAPI.
	•	Dependencies:
	•	Node.js for frontend.
	•	Python with required libraries for backend (see requirements.txt).

Screenshots

Homepage

Debate in Progress

Contact

For questions, suggestions, or collaborations, feel free to reach out through GitHub issues. Let’s work together to build more innovative AI tools!
