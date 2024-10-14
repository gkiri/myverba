"use client";

import React, { useState, FC } from 'react';
import { SettingsConfiguration } from '@/types/settings';
import PulseLoader from 'react-spinners/PulseLoader';
import { FaFileImport } from "react-icons/fa";

interface AddMocksPageProps {
  settingConfig: SettingsConfiguration;
  APIHost: string | null;
}

const AddMocksPageClient: FC<AddMocksPageProps> = ({ settingConfig, APIHost }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null); 
  const [uploadError, setUploadError] = useState<string | null>(null); 

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    } else {
      setSelectedFile(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadMessage(null); 
      setUploadError('Please select a JSON file to upload.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadMessage('Uploading...');
    setUploadError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch(`${settingConfig.APIHost}/api/upload_mock_exam`, {
        method: 'POST',
        body: formData,
        // Note: The native fetch API does not support onUploadProgress.
        // Consider using Axios if upload progress tracking is required.
      });

      if (response.ok) {
        const data = await response.json();
        setUploadMessage(data.message || 'Mock exam questions uploaded successfully!'); 
        setUploadError(null);
      } else {
        const errorData = await response.json(); 
        setUploadMessage(null);
        setUploadError(errorData.error || 'Error uploading mock exam questions.');
      }
    } catch (error) {
      console.error("Error uploading file: ", error);
      setUploadMessage(null);
      setUploadError('An error occurred during upload.'); 
    } finally {
      setIsUploading(false);
      setSelectedFile(null); // Reset selected file
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-5"> 
      <h2 className="text-2xl font-bold mb-8 text-text-verba">Add Mock Exam Questions</h2>

      {/* File Upload Area */}
      <div className="flex flex-col gap-4 w-full md:w-1/2 lg:w-1/3 bg-bg-alt-verba p-8 rounded-lg shadow-lg">
        <input 
          type="file" 
          accept=".json" //  Only accept JSON files
          onChange={handleFileChange} 
          className="file-input file-input-bordered w-full"
        />

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="btn btn-lg text-base flex gap-2 bg-secondary-verba hover:bg-button-hover-verba text-text-verba"
        >
          {isUploading ? ( //  Show uploading state
            <>
              <PulseLoader color={settingConfig.Customization.settings.text_color.color} loading={true} size={10} speedMultiplier={0.75} />
              Uploading... 
            </> 
          ) : ( // Show default button state
            <>
              <FaFileImport />  
              Upload Questions
            </>
          )} 
        </button>

        {/* Progress Bar (Optional) - Uncomment to enable */}
        {/* 
        {isUploading && (
          <progress className="progress progress-primary w-full" value={uploadProgress} max="100"></progress>
        )} 
        */}

        {/* Display Messages */}
        {uploadMessage && <p className="text-green-500">{uploadMessage}</p>} 
        {uploadError && <p className="text-red-500">{uploadError}</p>} 
      </div>
    </div>
  );
};

export default AddMocksPageClient;
