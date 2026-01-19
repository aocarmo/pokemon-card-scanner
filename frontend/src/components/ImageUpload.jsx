// FILE: src/components/ImageUpload.jsx
import { useState, useRef } from 'react';

export default function ImageUpload({ onUpload, loading }) {
  const [debug, setDebug] = useState(false);
  const [preview, setPreview] = useState(null);
  const inputRef = useRef();

  const handleChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = () => {
    const file = inputRef.current?.files[0];
    if (file) {
      onUpload(file, debug);
    }
  };

  return (
    <div className="upload">
      <input
        type="file"
        accept="image/*"
        ref={inputRef}
        onChange={handleChange}
      />
      <label>
        <input
          type="checkbox"
          checked={debug}
          onChange={(e) => setDebug(e.target.checked)}
        />
        Debug mode
      </label>
      <button onClick={handleSubmit} disabled={loading}>
        {loading ? 'Scanning...' : 'Scan Card'}
      </button>
      {preview && <img src={preview} alt="Preview" className="preview" />}
    </div>
  );
}
