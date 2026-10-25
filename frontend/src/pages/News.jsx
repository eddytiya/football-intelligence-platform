import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import MainLayout from "../components/layout/MainLayout";
import FootballLoader from "../components/layout/FootballLoader";
import { getNews } from "../api/newsApi";
import { getAccountFavourites } from "../api/accountApi";
import { getTeamProfile } from "../api/teamApi";
import "./News.css";
import { TbBallFootball } from "react-icons/tb";

const timeAgo = (value) => {
    if (!value) return "";
    const hours = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 3600000));
    if (hours < 1) return "just now";
    if (hours < 24) return `${hours}h ago`;
    return `${Math.round(hours / 24)}d ago`;
};

function News() {
    const [searchParams] = useSearchParams();
    const initialClub = searchParams.get("club") || "";
    const [followedClubs, setFollowedClubs] = useState([]);
    const [selected, setSelected] = useState(initialClub);
    const [searchTerm, setSearchTerm] = useState(initialClub);
    const [feed, setFeed] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const club = searchParams.get("club") || "";
        setSelected(club);
        setSearchTerm(club);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams.get("club")]);

    useEffect(() => {
        getAccountFavourites().then((rows) => {
            const teamIds = rows.filter((row) => row.entity_type === "team").map((row) => row.entity_id);
            return Promise.all(teamIds.map((id) => getTeamProfile(id).catch(() => null)));
        }).then((profiles) => setFollowedClubs(profiles.filter(Boolean))).catch(() => setFollowedClubs([]));
    }, []);

    useEffect(() => {
        let active = true;
        setLoading(true);
        const load = () => getNews({ query: selected }).then((data) => {
            if (active) setFeed(data);
        }).catch(() => active && setFeed({ articles: [], error: "The news feed is temporarily unavailable." })).finally(() => active && setLoading(false));
        load();
        const timer = window.setInterval(load, 180000);
        return () => { active = false; window.clearInterval(timer); };
    }, [selected]);

    return <MainLayout><section className="news-page">
        <header className="news-hero">
            <div><span>Matchday reading</span><h1>News</h1><p>Real football headlines, or look up any club, country or competition.</p></div>
            <div className="news-hero-controls">
                <form className="news-search" onSubmit={(event) => { event.preventDefault(); setSelected(searchTerm.trim()); }}>
                    <input value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Search a club, country or competition..." />
                    <button type="submit">Search</button>
                </form>
                <select value={selected} onChange={(event) => { setSelected(event.target.value); setSearchTerm(event.target.value); }}>
                    <option value="">Football news</option>
                    {followedClubs.map((club) => <option key={club.id} value={club.name}>{club.name}</option>)}
                </select>
            </div>
        </header>

        {loading ? <FootballLoader label="Loading the latest headlines" /> : feed?.error ? <div className="news-empty"><p>{feed.error}</p></div> : !feed?.articles?.length ? <div className="news-empty"><p>No recent headlines found{selected ? ` for ${selected}` : ""}.</p></div> : <div className="news-grid">
            {feed.articles.map((article, index) => <a className="news-card" href={article.url} target="_blank" rel="noreferrer" key={`${article.url}-${index}`}>
                {article.image ? <img src={article.image} alt="" /> : <div className="news-card-fallback"><TbBallFootball aria-hidden="true" /></div>}
                <div className="news-card-body">
                    <span>{article.source || "Football news"} · {timeAgo(article.published_at)}</span>
                    <strong>{article.title}</strong>
                    {article.description && <p>{article.description}</p>}
                </div>
            </a>)}
        </div>}
    </section></MainLayout>;
}

export default News;
