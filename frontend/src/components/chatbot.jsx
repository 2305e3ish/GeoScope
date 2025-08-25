import React, { useRef, useEffect } from 'react';

import './chatbot.css';

const Chatbot = () => {
  const chatMessagesRef = useRef(null);
  const userInputRef = useRef(null);

  useEffect(() => {
    // Initial bot message
    appendMessage('Hello! Tell me about an Earth event you\'re interested in (e.g., volcano eruption), and I\'ll recommend relevant NASA datasets.', 'bot-message');
  }, []);

  const sendMessage = () => {
    const messageText = userInputRef.current.value.trim();
    if (!messageText) return;

    appendMessage(messageText, 'user-message');
    userInputRef.current.value = '';

    setTimeout(() => {
      const botResponse = getBotResponse(messageText);
      appendMessage(botResponse, 'bot-message');
    }, 1000);
  };

  const appendMessage = (text, className) => {
    const message = document.createElement('div');
    message.classList.add('message', className);
    message.textContent = text;
    chatMessagesRef.current.appendChild(message);
    chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
  };

  const getBotResponse = (userMessage) => {
    const lowerMessage = userMessage.toLowerCase();
    if (lowerMessage.includes('volcano')) {
      return 'For volcano eruptions, I recommend: ASTER for land surface temperature and elevation[](https://asterweb.jpl.nasa.gov/), MODIS for aerosols and fire[](https://modis.gsfc.nasa.gov/data/). Check NASA Earthdata Search: https://search.earthdata.nasa.gov';
    } else if (lowerMessage.includes('flood')) {
      return 'For floods, try GPM for rainfall[](https://gpm.nasa.gov/data) or SMAP for soil moisture[](https://smap.jpl.nasa.gov/data/). Visualize in Giovanni: https://giovanni.gsfc.nasa.gov/';
    } else if (lowerMessage.includes('fire') || lowerMessage.includes('forest fire')) {
      return 'For forest fires, MODIS is great for fire and vegetation[](https://modis.gsfc.nasa.gov/data/). Also, check Earth Observatory stories: https://earthobservatory.nasa.gov';
    } else if (lowerMessage.includes('earthquake')) {
      return 'Earthquakes might use Sentinel for land changes[](https://scihub.copernicus.eu/). Search NASA ESDS for more: https://earthdata.nasa.gov/esds';
    } else {
      return 'Sorry, I didn\'t recognize that event. Try describing a natural disaster like "volcano", "flood", or "fire".';
    }
  };

  return (
    <div className="chat-container">
      <div id="particles-js"></div>
      <div className="chat-header">
        <h2>Earth Event Dataset Recommender</h2>
        <p>Ask about natural events like volcanoes, floods, or fires!</p>
      </div>
      <div className="chat-messages" ref={chatMessagesRef}></div>
      <div className="chat-input">
        <input type="text" ref={userInputRef} placeholder="Type your message..." />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

export default Chatbot;