document.getElementById("uploadForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    document.getElementById("loader").classList.remove("hidden");
    document.getElementById("audioPlayer").classList.add("hidden");

    fetch("/process", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("loader").classList.add("hidden");

        if (data.error) {
            alert(data.error);
            return;
        }

        document.getElementById("extractedText").innerText = data.extracted_text;
        document.getElementById("translatedText").innerText = data.translated_text;

        const audioPlayer = document.getElementById("audioPlayer");
        audioPlayer.src = "data:audio/mp3;base64," + data.audio_base64;
        audioPlayer.classList.remove("hidden");
        audioPlayer.play();
    })
    .catch(err => {
        document.getElementById("loader").classList.add("hidden");
        alert("Something went wrong!");
        console.error(err);
    });
});