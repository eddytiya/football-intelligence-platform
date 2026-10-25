import { useEffect, useRef, useState } from "react";

import { getNotifications, markAllNotificationsRead, markNotificationRead } from "../../api/notificationApi";
import "./NotificationBell.css";
import { FiBell } from "react-icons/fi";

const timeAgo = (value) => {
    const minutes = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 60000));
    if (minutes < 1) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.round(hours / 24)}d ago`;
};

function NotificationBell() {
    const containerRef = useRef(null);
    const [notifications, setNotifications] = useState([]);
    const [open, setOpen] = useState(false);

    useEffect(() => {
        let active = true;
        const load = () => getNotifications().then((data) => active && setNotifications(data)).catch(() => {});
        load();
        const timer = window.setInterval(load, 60000);
        return () => { active = false; window.clearInterval(timer); };
    }, []);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) setOpen(false);
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const unreadCount = notifications.filter((item) => !item.read_at).length;

    const openItem = (item) => {
        if (!item.read_at) {
            markNotificationRead(item.id).then(() => {
                setNotifications((current) => current.map((entry) => entry.id === item.id ? { ...entry, read_at: new Date().toISOString() } : entry));
            }).catch(() => {});
        }
    };

    const readAll = () => {
        markAllNotificationsRead().then(() => {
            setNotifications((current) => current.map((entry) => ({ ...entry, read_at: entry.read_at || new Date().toISOString() })));
        }).catch(() => {});
    };

    return <div className="notification-bell" ref={containerRef}>
        <button type="button" className="notification-bell-trigger" onClick={() => setOpen((value) => !value)} aria-label="Notifications" aria-expanded={open}>
            <FiBell />{unreadCount > 0 && <span className="notification-bell-badge">{unreadCount > 9 ? "9+" : unreadCount}</span>}
        </button>
        {open && <div className="notification-bell-menu">
            <header><span>Notifications</span>{unreadCount > 0 && <button type="button" onClick={readAll}>Mark all read</button>}</header>
            {notifications.length ? <div className="notification-bell-list">
                {notifications.map((item) => <button type="button" key={item.id} className={item.read_at ? "" : "is-unread"} onClick={() => openItem(item)}>
                    <strong>{item.title}</strong>
                    <span>{item.body}</span>
                    <small>{timeAgo(item.created_at)}</small>
                </button>)}
            </div> : <p className="notification-bell-empty">No notifications yet. Add a match to your watchlist to get kick-off reminders and results here.</p>}
        </div>}
    </div>;
}

export default NotificationBell;
