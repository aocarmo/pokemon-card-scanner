// FILE: src/components/ConfirmModal.jsx
export default function ConfirmModal({ result, onConfirm, onCancel }) {
  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Card Detected!</h2>
        <table>
          <tbody>
            <tr><td>Name:</td><td>{result.name}</td></tr>
            <tr><td>Collection:</td><td>{result.set || 'unknown'}</td></tr>
            <tr><td>Number:</td><td>{result.number}</td></tr>
            <tr><td>Language:</td><td>{result.language || 'unknown'}</td></tr>
            <tr><td>Confidence:</td><td>{(result.confidence * 100).toFixed(1)}%</td></tr>
          </tbody>
        </table>
        <div className="modal-buttons">
          <button className="confirm-btn" onClick={onConfirm}>✓ Confirm & Save</button>
          <button className="cancel-btn" onClick={onCancel}>✕ Cancel</button>
        </div>
      </div>
    </div>
  );
}
