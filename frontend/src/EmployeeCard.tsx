import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const API_BASE_URL = '/api'; // Use relative path for flexibility

const EmployeeCard = () => {
  const [employeeCards, setEmployeeCards] = useState<any>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/employee_cards`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setEmployeeCards(data);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="container mt-5">
        <h1>Karty Pracowników</h1>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p>Ładowanie danych...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mt-5">
        <h1>Karty Pracowników</h1>
        <div className="alert alert-danger" role="alert">
          Błąd podczas ładowania danych: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-5">
      <h1>Karty Pracowników</h1>

      {Object.keys(employeeCards).length > 0 ? (
        <div className="row">
          {Object.entries(employeeCards).map(([id, card]: [string, any]) => (
            <div className="col-md-4 mb-4" key={id}>
              <div className="card">
                <div className="card-body">
                  <h5 className="card-title">{card.imie_nazwisko} ({id})</h5>
                  <p className="card-text">Wiek: {card.wiek}</p>
                  <p className="card-text">Pochodzenie: {card.pochodzenie}</p>
                  <p className="card-text">Stanowisko: {card.stanowisko}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>Brak kart pracowników do wyświetlenia.</p>
      )}
    </div>
  );
};

export default EmployeeCard;
