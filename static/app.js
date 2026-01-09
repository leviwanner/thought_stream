document.addEventListener("DOMContentLoaded", () => {
  const thoughtInput = document.getElementById("thought-input");
  const submitButton = document.getElementById("submit-thought");
  const feed = document.getElementById("feed");
  const newerButton = document.getElementById("newer-thoughts");
  const olderButton = document.getElementById("older-thoughts");
  const subscribeButton = document.getElementById("subscribe");

  let currentPage = 1;

  function linkify(text) {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.replace(urlRegex, (url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
    });
  }

  function isImageUrl(url) {
    if (typeof url !== "string") return false;

    // This check handles both absolute and relative URLs that end in an image extension
    if (url.match(/\.(jpeg|jpg|gif|png|webp|avif)$/i)) {
      return true;
    }

    // This handles special cases like Twitter that use query parameters for format
    if (url.includes("format=jpg") || url.includes("format=png")) {
      return true;
    }
    return false;
  }

  async function getThoughts(page = 1) {
    const response = await fetch(`/thoughts?page=${page}`);
    const data = await response.json();

    feed.innerHTML = "";
    data.thoughts.forEach((thought) => {
      const thoughtElement = document.createElement("div");
      thoughtElement.classList.add("thought");

      const content = thought.text.trim();
      if (isImageUrl(content)) {
        const anchorElement = document.createElement("a");
        anchorElement.href = content;
        anchorElement.target = "_blank";
        anchorElement.rel = "noopener noreferrer"; // Security best practice
        const imageElement = document.createElement("img");
        imageElement.src = content;
        imageElement.classList.add("thought-image");
        anchorElement.appendChild(imageElement);
        thoughtElement.appendChild(anchorElement);
      } else {
        const textContainer = document.createElement("span"); // Use a container to hold innerHTML
        textContainer.innerHTML = linkify(thought.text); // Use innerHTML to render links
        thoughtElement.appendChild(textContainer);
      }

      const dateElement = document.createElement("span");
      dateElement.classList.add("thought-date");
      const date = new Date(thought.timestamp); // FIX: Removed the extra '+ "Z"'
      dateElement.textContent = date.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      });

      thoughtElement.appendChild(dateElement);
      feed.appendChild(thoughtElement);
    });

    // Update pagination button visibility
    olderButton.style.display = data.has_next ? "block" : "none";
    newerButton.style.display = data.has_prev ? "block" : "none";
    currentPage = data.page;
  }

  async function postThought() {
    const thought = thoughtInput.value;
    if (thought) {
      await fetch("/thoughts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thought }),
      });
      thoughtInput.value = "";
      getThoughts(1); // Go back to the first page to see the new post
    }
  }

  function showOlder() {
    getThoughts(currentPage + 1);
  }

  function showNewer() {
    getThoughts(currentPage - 1);
  }

  async function subscribeToPush() {
    const response = await fetch("/vapid_public_key");
    const data = await response.json();
    const publicKey = data.public_key;

    navigator.serviceWorker.ready.then((registration) => {
      registration.pushManager
        .subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(publicKey),
        })
        .then((subscription) => {
          fetch("/subscription", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(subscription),
          });
        });
    });
  }

  // Helper function to convert base64 string to Uint8Array
  function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, "+")
      .replace(/_/g, "/");

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }


  thoughtInput.addEventListener('paste', async (e) => {
    // Check if pasted items contain an image
    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
    let imageFile = null;
    for (const item of items) {
        if (item.kind === 'file' && item.type.startsWith('image/')) {
            imageFile = item.getAsFile();
            break;
        }
    }

    if (imageFile) {
        e.preventDefault(); // Prevent pasting file name as text
        thoughtInput.placeholder = "Uploading image..."; // Provide feedback

        const formData = new FormData();
        formData.append('file', imageFile);

        try {
            const response = await fetch('/upload_image', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const data = await response.json();
            thoughtInput.value = data.url; // Set textarea value to the new image URL
            thoughtInput.placeholder = "What's on your mind?";
        } catch (error) {
            console.error('Error uploading image:', error);
            thoughtInput.placeholder = "Upload failed. Please try again.";
        }
    }
  });

  // Event Listeners
  submitButton.addEventListener("click", postThought);
  olderButton.addEventListener("click", showOlder);
  newerButton.addEventListener("click", showNewer);
  subscribeButton.addEventListener("click", subscribeToPush);

  // Initial Load
  getThoughts(1);

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/static/sw.js").then(
        (registration) => {
          console.log(
            "ServiceWorker registration successful with scope: ",
            registration.scope
          );
        },
        (err) => {
          console.log("ServiceWorker registration failed: ", err);
        }
      );
    });
  }
});
