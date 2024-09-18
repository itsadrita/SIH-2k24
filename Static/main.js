import * as THREE from 'https://cdn.skypack.dev/three@0.132.2';

// Access DOM elements
var label = document.getElementById("label");
var container = document.getElementById("container");

// Set up the scene, camera, and renderer
const fov = 75;
const aspect = container.clientWidth / container.clientHeight;
const near = 0.1;
const far = 1000;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x253238);

const camera = new THREE.PerspectiveCamera(fov, aspect, near, far);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);

// Resize the renderer when the window is resized
window.addEventListener('resize', () => {
    const width = container.clientWidth;
    const height = container.clientHeight;
    renderer.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
});

// Variables for handling word input and animation frames
var wordList = [];
var wordidx = 0;
var frameidx = 0;

// Handle form submission to capture and split the input message
var textForm = document.getElementById("inputForm");
textForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var message = document.getElementById("message").value;
    wordList = message.split(" ");
    frameidx = 0;
    wordidx = 0;
    console.log(wordList);
});

// Handle speech-to-text
var micBtn = document.getElementById('mic-btn');
if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    micBtn.addEventListener('click', function () {
        recognition.start();
        micBtn.textContent = '🎤 Listening...';
    });

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById("message").value = transcript;
        micBtn.textContent = '🎤 Start Speaking';
        // Trigger form submission to update animation
        textForm.dispatchEvent(new Event('submit'));
    };

    recognition.onerror = function (event) {
        console.error('Speech recognition error detected: ' + event.error);
        micBtn.textContent = '🎤 Start Speaking';
    };

    recognition.onend = function () {
        micBtn.textContent = '🎤 Start Speaking';
    };
} else {
    alert('Your browser does not support speech recognition.');
}

// Fetch JSON data (modify the path if needed)
fetch('static/json/finalC.json')
    .then(response => response.json())
    .then(data => {
        // Function to draw a point (joint)
        function drawPoint(x, y, z) {
            const pointRadius = 0.25;
            const geometry = new THREE.SphereGeometry(pointRadius, 32, 16);
            const material = new THREE.MeshBasicMaterial({ color: 0x84FFFF });
            const sphere = new THREE.Mesh(geometry, material);
            scene.add(sphere);
            sphere.position.set(x, y, z);
        }

        // Function to draw a line between two points (bones)
        function drawLine(x1, y1, z1, x2, y2, z2) {
            const points = [
                new THREE.Vector3(x1, y1, z1),
                new THREE.Vector3(x2, y2, z2)
            ];
            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const material = new THREE.LineBasicMaterial({ color: 0xFFFFFF });
            const line = new THREE.Line(geometry, material);
            scene.add(line);
        }

        // Function to redistribute elements if one hand has more than 21 points
        function redistributeElements(left, right) {
            if (left.length > 21) {
                right.push(...left.splice(21));
            } else if (right.length > 21) {
                left.push(...right.splice(21));
            }
        }

        // Function to connect joints with lines
        function connectLines(frameidx) {
            const edgeList = [
                [0, 1], [1, 2], [2, 3], [3, 4], [0, 5],
                [5, 6], [6, 7], [7, 8], [5, 9], [9, 10],
                [10, 11], [11, 12], [9, 13], [13, 14],
                [14, 15], [15, 16], [13, 17], [17, 18],
                [18, 19], [19, 20], [0, 17]
            ];

            var left = data[wordList[wordidx]][frameidx]['Left Hand Coordinates'];
            var right = data[wordList[wordidx]][frameidx]['Right Hand Coordinates'];

            redistributeElements(left, right);

            edgeList.forEach(function (edge) {
                const [u, v] = edge;
                if (left[u] && left[v]) {
                    const [lx1, ly1, lz1] = left[u]['Coordinates'];
                    const [lx2, ly2, lz2] = left[v]['Coordinates'];
                    drawLine(lx1 * 50, ly1 * -50, lz1 * 50, lx2 * 50, ly2 * -50, lz2 * 50);
                }
                if (right[u] && right[v]) {
                    const [rx1, ry1, rz1] = right[u]['Coordinates'];
                    const [rx2, ry2, rz2] = right[v]['Coordinates'];
                    drawLine(rx1 * 50, ry1 * -50, rz1 * 50, rx2 * 50, ry2 * -50, rz2 * 50);
                }
            });
        }

        // Setup clock and delta time for controlling frame rate
        let clock = new THREE.Clock();
        let delta = 0;
        let interval = 1 / 30; // 45 FPS

        // Rendering function
        function render() {
            requestAnimationFrame(render);
            delta += clock.getDelta();

            if (delta > interval) {
                delta = delta % interval;

                if (wordList.length > 0 && wordidx < wordList.length) {
                    label.innerHTML = wordList[wordidx].toUpperCase();

                    var left = data[wordList[wordidx]][frameidx]['Left Hand Coordinates'];
                    var right = data[wordList[wordidx]][frameidx]['Right Hand Coordinates'];

                    left.forEach(joint => {
                        drawPoint(joint['Coordinates'][0] * 50, joint['Coordinates'][1] * -50, joint['Coordinates'][2] * 50);
                    });

                    right.forEach(joint => {
                        drawPoint(joint['Coordinates'][0] * 50, joint['Coordinates'][1] * -50, joint['Coordinates'][2] * 50);
                    });

                    connectLines(frameidx);

                    frameidx++;
                    if (frameidx >= data[wordList[wordidx]].length) {
                        frameidx = 0;
                        wordidx++;
                        if (wordidx < wordList.length) {
                            label.innerHTML = wordList[wordidx].toUpperCase();
                        }
                    }
                } else {
                    label.innerHTML = "N/A";
                }

                renderer.render(scene, camera);
                // Efficiently clear the scene
                scene.remove.apply(scene, scene.children);
            }
        }

        render();
    });

// Adjust the camera position to better view the scene
camera.position.set(27.5, -30, 25);
