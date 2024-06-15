
// Get all buttons with class 'compress-button'
const compressButtons = document.querySelectorAll('.compress-button');

// Add event listener to each button
compressButtons.forEach(button => {
    button.addEventListener('click', function() {
        // Toggle the 'active' class on button click
        this.classList.toggle('active');

        // After a short delay, remove the 'active' class
        setTimeout(() => {
            this.classList.remove('active');
        }, 100);
    });
});



function showMessageBox(msg) {
    console.log("Showing message box with message:", msg);
    var messageBox = document.getElementById("messageBox");

    // Show the message box
    messageBox.style.display = "block";

    // Set the message text
    var messageText = document.getElementById("messageText");
    messageText.textContent = msg;

    // Hide the message box after 3 seconds (3000 milliseconds)
    setTimeout(function() {
        console.log("Hiding message box");
        messageBox.style.display = "none";
    }, 3000);
}

var recoveryCode = "{{ random_code2 }}"; // Get the recovery code from Flask
    
    document.getElementById('codeInput').addEventListener('input', function() {
        var codeInput = document.getElementById('codeInput').value;
        if (codeInput === recoveryCode) {
            document.getElementById('passwordInput').disabled = false;
            document.getElementById('confirmPasswordInput').disabled = false;
        } else {
            document.getElementById('passwordInput').disabled = true;
            document.getElementById('confirmPasswordInput').disabled = true;
        }
    });



const button = document.getElementById('myButton');
let isClicked = false;

button.addEventListener('click', () => {
  if (!isClicked) {
    // Your action to perform once
    console.log("Button clicked!");
    isClicked = true;
  } else {
    console.log("Button already clicked!");
  }
});

