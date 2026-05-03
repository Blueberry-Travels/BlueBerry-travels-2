import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import api from '../lib/api';

interface BlogPost {
  slug: string;
  title: string;
  short_desc: string;
  author: string;
  published_at: string;
  tags: string[];
  image_url: string;
  body?: string;
}

const TAG_COLORS: Record<string, string> = {
  trekking: '#1B6B3A',
  adventure: '#7C3AED',
  culture: '#D97706',
  nature: '#00796B',
};

export default function Blog() {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<BlogPost | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    const fetchPosts = async () => {
        try {
            const res = await api.get('/api/v1/blogs/');
            if (res.data?.posts) setPosts(res.data.posts);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };
    fetchPosts();
  }, []);

  const openPost = async (slug: string) => {
    setLoadingDetail(true);
    try {
      const res = await api.get(`/api/v1/blogs/${slug}/`);
      setSelected(res.data);
    } catch { /* Non-fatal */ }
    finally { setLoadingDetail(false); }
  };

  return (
    <>
      <Head>
        <title>Travel Stories — Blueberry Travels</title>
      </Head>

      <div className="hero-image" style={{ backgroundImage: `url('/hero_blog.png')`, height: '50vh', minHeight: '400px' }}>
          <div className="hero-overlay"></div>
          <div className="hero-content">
              <span className="hero-badge">Journal</span>
              <h1 className="hero-title" style={{ fontSize: 'clamp(40px, 8vw, 72px)' }}>Travel Stories</h1>
              <p className="hero-subtitle">Chronicles from the high passes, local wisdom, and field notes from our explorers.</p>
          </div>
      </div>

      <div className="blog-container">
          {loading ? (
              <div className="loading-grid">
                  {[1,2,3].map(i => <div key={i} className="skeleton-card glass"></div>)}
              </div>
          ) : posts.length === 0 ? (
              <div className="empty-state glass">
                  <div className="e-icon">📖</div>
                  <p>Our story archives are currently being curated. Check back soon for fresh chronicles.</p>
              </div>
          ) : (
              <div className="post-grid">
                  {posts.map((post, idx) => (
                      <div key={post.slug} className="post-card glass" onClick={() => openPost(post.slug)}>
                          <div className="post-thumb" style={{ background: `linear-gradient(135deg, rgba(76,124,53,0.2), rgba(10,10,12,0.5))` }}>
                              <span className="post-emoji">🌿</span>
                          </div>
                          <div className="post-body">
                              <div className="post-tags">
                                  {post.tags.map(t => <span key={t} className="post-tag">#{t}</span>)}
                              </div>
                              <h2 className="post-title">{post.title}</h2>
                              <p className="post-excerpt">{post.short_desc}</p>
                              <div className="post-footer">
                                  <span className="post-author">By {post.author}</span>
                                  <span className="post-date">{post.published_at}</span>
                              </div>
                          </div>
                      </div>
                  ))}
              </div>
          )}
      </div>

      {selected && (
          <div className="modal-backdrop" onClick={() => setSelected(null)}>
              <div className="modal-content glass-dark" onClick={e => e.stopPropagation()}>
                  <div className="modal-close" onClick={() => setSelected(null)}>✕</div>
                  <div className="modal-body">
                      <div className="post-tags">
                          {selected.tags.map(t => <span key={t} className="post-tag">#{t}</span>)}
                      </div>
                      <h1 className="modal-title">{selected.title}</h1>
                      <div className="modal-meta">By {selected.author} &nbsp;·&nbsp; {selected.published_at}</div>
                      <div className="modal-rich-text" dangerouslySetInnerHTML={{ __html: selected.body?.replace(/\n/g, '<br/>') || '' }} />
                      <div className="modal-actions">
                          <button className="btn-primary" onClick={() => setSelected(null)}>Back to Stories</button>
                      </div>
                  </div>
              </div>
          </div>
      )}

      <style jsx>{`
        .blog-container {
            max-width: var(--main-width);
            margin: -80px auto 100px;
            padding: 0 var(--outer-gap);
            position: relative;
            z-index: 10;
        }
        
        .post-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 32px;
        }
        
        .post-card {
            border-radius: 32px; overflow: hidden; cursor: pointer;
            transition: var(--transition-smooth);
        }
        .post-card:hover { transform: translateY(-8px); border-color: var(--primary-light); }
        
        .post-thumb { height: 200px; display: flex; align-items: center; justify-content: center; }
        .post-emoji { font-size: 48px; filter: drop-shadow(0 0 20px rgba(76,124,53,0.3)); }
        
        .post-body { padding: 32px; }
        .post-tags { display: flex; gap: 8px; margin-bottom: 16px; }
        .post-tag { font-size: 11px; font-weight: 800; color: var(--primary-light); text-transform: uppercase; letter-spacing: 0.1em; }
        
        .post-title { font-size: 22px; color: white; margin-bottom: 12px; line-height: 1.3; }
        .post-excerpt { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 24px; }
        
        .post-footer { display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: var(--text-muted); font-weight: 600; }
        
        .loading-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 32px; }
        .skeleton-card { height: 400px; border-radius: 32px; }
        
        .modal-backdrop {
            position: fixed; inset: 0; background: rgba(10,10,12,0.8);
            backdrop-filter: blur(12px); z-index: 2000;
            display: flex; align-items: center; justify-content: center;
            padding: 40px 24px;
        }
        .modal-content {
            width: 100%; max-width: 800px; max-height: 90vh;
            border-radius: 40px; overflow-y: auto; position: relative;
        }
        .modal-close { position: absolute; top: 24px; right: 24px; font-size: 20px; color: var(--text-muted); cursor: pointer; z-index: 5; }
        .modal-body { padding: 56px; }
        .modal-title { font-size: clamp(32px, 5vw, 48px); color: white; margin-bottom: 16px; line-height: 1.1; letter-spacing: -0.02em; }
        .modal-meta { font-size: 14px; color: var(--text-muted); margin-bottom: 40px; }
        .modal-rich-text { font-size: 17px; line-height: 1.8; color: var(--text-secondary); }
        .modal-actions { margin-top: 48px; padding-top: 40px; border-top: 1px solid var(--glass-border); }
        
        .empty-state { padding: 80px; text-align: center; border-radius: 40px; }
        .e-icon { font-size: 64px; margin-bottom: 24px; }
        .empty-state p { font-size: 18px; color: var(--text-secondary); max-width: 500px; margin: 0 auto; }
      `}</style>
    </>
  );
}
