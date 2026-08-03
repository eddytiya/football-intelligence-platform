import "./Hero.css";

function Hero() {
    return (
        <section className="hero">

            {/* Stadium Lighting */}
            <div className="stadium-light"></div>

            {/* Football Pitch */}
            <div className="pitch">

                <div className="center-line"></div>

                <div className="center-circle"></div>

                <div className="center-spot"></div>

                <div className="penalty-box left"></div>

                <div className="penalty-box right"></div>

                <div className="goal-box left"></div>

                <div className="goal-box right"></div>

            </div>

            {/* Hero Content */}
            <div className="hero-content">

                {/* Left Side */}
                <div className="hero-card">

                    <span className="hero-tag">
                        AI-Powered Football Analytics
                    </span>

                    <h1>
                        Football Intelligence Platform
                    </h1>

                    <p>
                        Predict football matches using Machine Learning,
                        ELO Ratings, Team Statistics, ELO Ratings and Advanced Match Analytics.
                    </p>

                    <div className="hero-buttons">

                        <button className="primary-btn">
                            Explore Predictions
                        </button>

                        <button className="secondary-btn">
                            View Dashboard
                        </button>

                    </div>

                </div>

                {/* Right Side */}

                <div className="hero-graphic">

                    <div className="prediction-card">

                        <div className="prediction-header">

                            <span className="live-badge">

                                LIVE

                            </span>

                            <h3>

                                Today's Prediction

                            </h3>

                        </div>

                        <div className="match-card">

                            <div className="team home">

                                <h4>Arsenal</h4>

                            </div>

                            <div className="vs">

                                VS

                            </div>

                            <div className="team away">

                                <h4>Chelsea</h4>

                            </div>

                        </div>

                        <div className="prediction-body">

                            <div className="prediction-row">

                                <span>Home Win</span>

                                <div className="prediction-progress">

                                    <div
                                        className="prediction-fill home"
                                        style={{ width: "62%" }}
                                    ></div>

                                </div>

                                <strong>62%</strong>

                            </div>

                            <div className="prediction-row">

                                <span>Draw</span>

                                <div className="prediction-progress">

                                    <div
                                        className="prediction-fill draw"
                                        style={{ width: "21%" }}
                                    ></div>

                                </div>

                                <strong>21%</strong>

                            </div>

                            <div className="prediction-row">

                                <span>Away Win</span>

                                <div className="prediction-progress">

                                    <div
                                        className="prediction-fill away"
                                        style={{ width: "17%" }}
                                    ></div>

                                </div>

                                <strong>17%</strong>

                            </div>

                        </div>

                        <div className="prediction-footer">

                            <div className="prediction-info">

                                <span>Confidence</span>

                                <strong>94%</strong>

                            </div>

                            <div className="prediction-info">

                                <span>Model</span>

                                <strong>LightGBM</strong>

                            </div>

                            <div className="prediction-info">

                                <span>Updated</span>

                                <strong>2 mins ago</strong>

                            </div>

                        </div>

                    </div>

                </div>

            </div>

            {/* Statistics */}

            <div className="hero-stats">

                <div className="stat-card">

                    <h2>512+</h2>

                    <p>Predictions</p>

                </div>

                <div className="stat-card">

                    <h2>LIVE</h2>

                    <p>Match Data</p>

                </div>

                <div className="stat-card">

                    <h2>13</h2>

                    <p>Competitions</p>

                </div>

                <div className="stat-card">

                    <h2>7</h2>

                    <p>AI Models</p>

                </div>

            </div>

        </section>
    );
}

export default Hero;
