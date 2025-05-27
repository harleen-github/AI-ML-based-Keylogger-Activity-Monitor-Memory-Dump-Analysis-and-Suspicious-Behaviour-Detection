# AI-ML-based-Keylogger-Activity-Monitor-Memory-Dump-Analysis-and-Suspicious-Behaviour-Detection
An intelligent, modular OS-level forensic tool for real-time detection of suspicious behavior using behavioral biometrics, memory dumps, and machine learning.

Developed as part of the BTech CSE OS Project — SE(OS)-VI-T165
| File                    | Purpose                                                       |
| ----------------------- | ------------------------------------------------------------- |
| activity\_tracker.py    | Logs detailed keystroke and mouse activity metrics            |
| live\_monitor.py        | Performs real-time behavior classification using ML           |
| model.py                | Trains and saves the Random Forest classifier                 |
| failedlogin\_logger.py  | Parses Windows Event Logs (ID 4625) for failed login attempts |
| dump\_trigger.py        | Automates memory dump creation for suspicious processes       |
| gui.py                  | Tkinter-based GUI for launching modules and monitoring        |
| rf\_model.joblib        | Trained Random Forest model                                   |
| scaler.joblib           | Fitted scaler for input feature normalization                 |
| normal\_abnormal.csv    | Labeled dataset for model training                            |
| activity\_metrics.csv   | Logged user activity for feature extraction                   |
| failed\_login\_logs.csv | Logs of detected failed login attempts                        |

#Key Features:
•	Keystrokes
•	Mouse activity
•	Failed login attempts
•	Memory dump extraction and analysis

👥 Authors
Saloni Gupta – 22022122 (Team Lead)
Harleen Kaur – 22022609
Srijan Chauhan – 22022739
