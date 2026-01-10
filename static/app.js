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
    console.log('Attempting to subscribe to push notifications...');
    
    try {
        console.log('Fetching VAPID public key...');
        const response = await fetch('/vapid_public_key');
        const data = await response.json();
        const publicKey = data.public_key;
        console.log('Successfully fetched VAPID public key.');

        const applicationServerKey = urlBase64ToUint8Array(publicKey);
        console.log('Final applicationServerKey to be used:', applicationServerKey);

        console.log('Waiting for service worker to be ready...');
        const registration = await navigator.serviceWorker.ready;
        console.log('Service worker is ready.');

        console.log('Subscribing push manager... (This should trigger the permission pop-up)');
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
        });
        console.log('Successfully subscribed:', subscription);

        console.log('Sending subscription to server...');
        await fetch('/subscription', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(subscription)
        });
        console.log('Subscription sent to server.');
        alert('Successfully subscribed to notifications!');

    } catch (error) {
        console.error('Failed to subscribe to push notifications:', error);
        alert(`Subscription failed. Please check the console for details. Error: ${error.name}`);
    }
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

  const refreshButton = document.getElementById('refresh-app');
  let newWorker;

  // --- PWA Update Handling ---
  function handleAppUpdates() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').then(reg => {
        reg.addEventListener('updatefound', () => {
          // A new service worker is installing
          newWorker = reg.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker is installed and waiting.
              // Update the UI to notify the user.
              refreshButton.textContent = 'New version available. Refresh!';
            }
          });
        });
      }).catch(err => {
        console.log('ServiceWorker registration failed: ', err);
      });

      // Reload the page once a new service worker has taken control
      let refreshing;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (refreshing) return;
        window.location.reload(true);
        refreshing = true;
      });
    }
  }

  // --- Event Listeners ---
  submitButton.addEventListener("click", postThought);
  olderButton.addEventListener("click", showOlder);
  newerButton.addEventListener("click", showNewer);
  subscribeButton.addEventListener("click", subscribeToPush);
  
  refreshButton.addEventListener('click', (e) => {
    e.preventDefault();
    if (newWorker) {
      // If a new worker is waiting, tell it to skip waiting
      newWorker.postMessage({ action: 'skipWaiting' });
    } else {
      // Otherwise, just perform a hard reload
      window.location.reload(true);
    }
  });


  // --- Initial Load ---
  getThoughts(1);
  handleAppUpdates();
});
