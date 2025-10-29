import cv2
from gestures.detector import recognize_gesture

def main():
    # Start webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Camera not accessible.")
        return

    print("Camera started. Press 'q' to quit.")  # removed emoji for Windows compatibility

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Flip the image for a mirror-like view
        frame = cv2.flip(frame, 1)

        # Process the frame to detect gesture
        gesture = recognize_gesture(frame)

        # Display recognized gesture on screen
        cv2.putText(frame, f"Gesture: {gesture}", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("AURA - Gesture Recognition", frame)

        # Quit when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Camera closed. Goodbye!")

if __name__ == "__main__":
    main()
