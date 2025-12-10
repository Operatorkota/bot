import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';

const API_BASE_URL = '/api'; // Use relative path for flexibility

const Home = () => (
  <div className="container mt-5">
    <h1>Witaj na stronie bota Discord!</h1>
    <p>Tutaj znajdziesz informacje o bocie i jego funkcjach.</p>
  </div>
);

const Dashboard = () => {
  const [patientCards, setPatientCards] = useState<any>({});
  const [userData, setUserData] = useState<any>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [patientCardsResponse, userDataResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/patient_cards`),
          fetch(`${API_BASE_URL}/user_data`)
        ]);

        if (!patientCardsResponse.ok) {
          throw new Error(`HTTP error! status: ${patientCardsResponse.status} for patient cards`);
        }
        if (!userDataResponse.ok) {
          throw new Error(`HTTP error! status: ${userDataResponse.status} for user data`);
        }

        const patientCardsData = await patientCardsResponse.json();
        const userDataData = await userDataResponse.json();

        setPatientCards(patientCardsData);
        setUserData(userDataData);
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
        <h1>Panel Informacyjny</h1>
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
        <h1>Panel Informacyjny</h1>
        <div className="alert alert-danger" role="alert">
          Błąd podczas ładowania danych: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-5">
      <h1>Panel Informacyjny</h1>
      <p>Wyświetlanie danych z botta:</p>

      <h2 className="mt-4">Karty Pacjentów</h2>
      {Object.keys(patientCards).length > 0 ? (
        <div className="row">
          {Object.entries(patientCards).map(([id, card]: [string, any]) => (
            <div className="col-md-4 mb-4" key={id}>
              <div className="card">
                <div className="card-body">
                  <h5 className="card-title">{card.imie_nazwisko} ({id})</h5>
                  <p className="card-text">Wiek: {card.wiek}</p>
                  <p className="card-text">Diagnoza: {card.diagnoza}</p>
                  <p className="card-text">Pokój: {card.pokoj}</p>
                  {/* Add more fields as needed */}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>Brak kart pacjentów do wyświetlenia.</p>
      )}

      <h2 className="mt-4">Dane Użytkowników</h2>
      {Object.keys(userData).length > 0 ? (
        <div className="row">
          {Object.entries(userData).map(([id, user]: [string, any]) => (
            <div className="col-md-4 mb-4" key={id}>
              <div className="card">
                <div className="card-body">
                  <h5 className="card-title">Użytkownik: {id}</h5>
                  <p className="card-text">Saldo: {user.balance || 'N/A'}</p>
                  <p className="card-text">Ilość kar: {user.sentences ? user.sentences.length : 0}</p>
                  {/* Add more fields as needed */}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>Brak danych użytkowników do wyświetlenia.</p>
      )}
    </div>
  );
};

const Commands = () => (
  <div className="container mt-5">
    <h1>Lista Komend</h1>
    <p>Tutaj znajdziesz wszystkie dostępne komendy bota.</p>
    <div className="alert alert-info" role="alert">
      Lista komend będzie wymagała ręcznego uzupełnienia lub implementacji API do ich pobierania z bota.
    </div>
    {/* Placeholder for commands list */}
  </div>
);

function App() {
  return (
    <Router>
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
        <div className="container-fluid">
          <Link className="navbar-brand" to="/">Discord Bot</Link>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav">
              <li className="nav-item">
                <Link className="nav-link" to="/">Strona Główna</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/dashboard">Dashboard</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/commands">Komendy</Link>
              </li>
            </ul>
          </div>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/commands" element={<Commands />} />
      </Routes>
    </Router>
  );
}

export default App;
