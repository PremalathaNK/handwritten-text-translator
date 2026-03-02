
const form = document.getElementById("uploadForm");
const loader = document.getElementById("loader");
const extractedText = document.getElementById("extractedText");
const translatedText = document.getElementById("translatedText");
const audioPlayer = document.getElementById("audioPlayer");

form.addEventListener("submit", async function (e) {
    e.preventDefault();

    // Reset UI
    loader.classList.remove("hidden");
    extractedText.innerText = "";
    translatedText.innerText = "";
    audioPlayer.classList.add("hidden");
    audioPlayer.src = "";

    const formData = new FormData(form);

    try {
        const response = await fetch("/process", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        loader.classList.add("hidden");

        if (data.error) {
            alert(data.error);
            return;
        }

        // Show text results
        extractedText.innerText = data.extracted_text;
        translatedText.innerText = data.translated_text;

        // Play audio (BASE64)
        audioPlayer.src = "data:audio/mp3;base64," + data.audio_base64;
        audioPlayer.classList.remove("hidden");
        audioPlayer.play();

    } catch (error) {
        loader.classList.add("hidden");
        alert("Something went wrong. Please try again.");
        console.error(error);
    }
});