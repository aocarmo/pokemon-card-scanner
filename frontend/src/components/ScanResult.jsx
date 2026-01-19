// FILE: src/components/ScanResult.jsx
export default function ScanResult({ result }) {
  return (
    <div className="result">
      <h2>Scan Result</h2>
      <table>
        <tbody>
          <tr><td>Name:</td><td>{result.name || '-'}</td></tr>
          <tr><td>Number:</td><td>{result.number || '-'}</td></tr>
          <tr><td>Set:</td><td>{result.set || '-'}</td></tr>
          <tr><td>Confidence:</td><td>{(result.confidence * 100).toFixed(1)}%</td></tr>
        </tbody>
      </table>
      {result.debug_image && (
        <div className="debug">
          <h3>Debug Image</h3>
          <img src={result.debug_image} alt="Debug" />
        </div>
      )}
    </div>
  );
}
