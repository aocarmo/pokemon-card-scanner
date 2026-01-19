// FILE: src/components/ScanResult.jsx
export default function ScanResult({ result }) {
  return (
    <div className="result">
      <h2>Scan Result</h2>
      <table>
        <tbody>
          <tr><td>Status:</td><td>{result.status}</td></tr>
          <tr><td>Name:</td><td>{result.name || '-'}</td></tr>
          <tr><td>Number:</td><td>{result.number || '-'}</td></tr>
          <tr><td>Collection:</td><td>{result.collection || '-'}</td></tr>
          <tr><td>Language:</td><td>
            {result.language === 'pt' ? 'Portuguese' : 
             result.language === 'en' ? 'English' : '-'}
          </td></tr>
          <tr><td>Confidence:</td><td>{((result.confidence || 0) * 100).toFixed(0)}%</td></tr>
        </tbody>
      </table>
    </div>
  );
}
