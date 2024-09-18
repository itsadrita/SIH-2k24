import mediapipe as mp
import cv2
import os
import json

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Folder containing video files
video_folder = '.\word videos'

# JSON file path to save the output
json_path = r'C:\Users\adrit\OneDrive\Desktop\New folder\SignWave\static\json\finalC.json'

# Default hand coordinates (zeros)
default_hand_coordinates = [{"Joint Index": i, "Coordinates": [0.0, 0.0, 0.0]} for i in range(21)]

# Initialize Hands model
with mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.5) as hands:
    # Create a dictionary to store the hand coordinates
    data = {}

    # Iterate over video files in the folder
    for idx, filename in enumerate(os.listdir(video_folder)):
        if filename.endswith(".mp4"):
            video_file = os.path.join(video_folder, filename)

            # Extract the file name without extension
            file_name = filename.split('.')[0]
            data[file_name] = []

            # Open video file
            cap = cv2.VideoCapture(video_file)

            frame_number = 0
            displayed_frame_count = 0  # To count the number of frames displayed

            while cap.isOpened():
                ret, frame = cap.read()

                if not ret:
                    break

                # Resize the frame to 800x750
                frame = cv2.resize(frame, (800, 750))

                # Convert the frame to RGB
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Detections
                results = hands.process(image_rgb)

                # Initialize hand coordinates with default (zeros)
                left_hand_coordinates = default_hand_coordinates.copy()
                right_hand_coordinates = default_hand_coordinates.copy()

                # Check if hand landmarks are detected
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        hand = hand_landmarks.landmark

                        # Determine handedness based on landmark positions
                        if hand[mp_hands.HandLandmark.WRIST].x < hand[mp_hands.HandLandmark.THUMB_CMC].x:
                            handedness = "Left"
                        else:
                            handedness = "Right"

                        # Store coordinates and joint index in the hand coordinates list
                        for joint_id, landmark in enumerate(hand):
                            x, y, z = landmark.x, landmark.y, landmark.z
                            joint_data = {
                                "Joint Index": joint_id,
                                "Coordinates": [x, y, z]
                            }
                            if handedness == "Left":
                                left_hand_coordinates[joint_id] = joint_data
                            else:
                                right_hand_coordinates[joint_id] = joint_data

                        # Draw landmarks on the frame
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                                  mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4),
                                                  mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2))

                    # Add frame data to the dictionary
                    data[file_name].append({
                        "Frame": frame_number,
                        "Left Hand Coordinates": left_hand_coordinates,
                        "Right Hand Coordinates": right_hand_coordinates
                    })

                    # Display every 10th video frame from the first 20 frames using OpenCV
                    if frame_number < 200 and frame_number % 10 == 0:  # Show frames only if frame number is less than 200 (20 frames at intervals of 10)
                        cv2.imshow('Frame', frame)
                        cv2.waitKey(1)  # Adjust the delay as needed
                        displayed_frame_count += 1

                    # Stop processing if 20 frames have been displayed
                    if displayed_frame_count >= 20:
                        break

                # Increment the frame number
                frame_number += 1

            cap.release()
            cv2.destroyAllWindows()

            # Print the current word during each loop iteration
            print(f"Processing video {idx + 1}: {file_name}")

    # Serialize the data dictionary to JSON and write it to the file
    with open(json_path, 'w') as json_file:
        json.dump(data, json_file)

# Open the JSON file for reading and load the data
with open(json_path, 'r') as json_file:
    data = json.load(json_file)

# Check for large gaps between frames and interpolate
for word in data:
    frames = data[word]
    num_frames = len(frames)

    if num_frames > 1:
        interpolated_frames = []

        for i in range(num_frames - 1):
            current_frame = frames[i]
            next_frame = frames[i + 1]

            if next_frame["Frame"] - current_frame["Frame"] > 1:
                # Compute the gap between frames
                gap = next_frame["Frame"] - current_frame["Frame"]

                # Interpolate hand coordinates for the gap frames
                for j in range(1, gap):
                    interpolation_ratio = j / gap

                    interpolated_left_hand_coordinates = []
                    interpolated_right_hand_coordinates = []

                    # Interpolate left hand coordinates
                    for joint_data in current_frame.get("Left Hand Coordinates", []):
                        current_coordinates = joint_data["Coordinates"]
                        next_coordinates = next_frame.get("Left Hand Coordinates", [])[joint_data["Joint Index"]]["Coordinates"]

                        interpolated_left_hand_coordinates.append({
                            "Joint Index": joint_data["Joint Index"],
                            "Coordinates": [
                                current_coordinates[0] + (next_coordinates[0] - current_coordinates[0]) * interpolation_ratio,
                                current_coordinates[1] + (next_coordinates[1] - current_coordinates[1]) * interpolation_ratio,
                                current_coordinates[2] + (next_coordinates[2] - current_coordinates[2]) * interpolation_ratio
                            ]
                        })

                    # Interpolate right hand coordinates
                    for joint_data in current_frame.get("Right Hand Coordinates", []):
                        current_coordinates = joint_data["Coordinates"]
                        next_coordinates = next_frame.get("Right Hand Coordinates", [])[joint_data["Joint Index"]]["Coordinates"]

                        interpolated_right_hand_coordinates.append({
                            "Joint Index": joint_data["Joint Index"],
                            "Coordinates": [
                                current_coordinates[0] + (next_coordinates[0] - current_coordinates[0]) * interpolation_ratio,
                                current_coordinates[1] + (next_coordinates[1] - current_coordinates[1]) * interpolation_ratio,
                                current_coordinates[2] + (next_coordinates[2] - current_coordinates[2]) * interpolation_ratio
                            ]
                        })

                    # Add interpolated frame to the list
                    interpolated_frames.append({
                        "Frame": current_frame["Frame"] + j,
                        "Left Hand Coordinates": interpolated_left_hand_coordinates,
                        "Right Hand Coordinates": interpolated_right_hand_coordinates
                    })

        # Append the interpolated frames to the original frames
        frames.extend(interpolated_frames)

# Serialize the updated data dictionary to JSON and write it to the file
with open(json_path, 'w') as json_file:
    json.dump(data, json_file)

print(f"Data has been saved and interpolated frames added to {json_path}")
