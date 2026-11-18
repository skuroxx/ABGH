package handler

import (
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// Handler proxies audio byte-ranges directly from upstream CDN to the client
// with zero disk storage (HTTP 206 Partial Content support for seeking).
func Handler(w http.ResponseWriter, r *http.Request) {
	rawURL := r.URL.Query().Get("url")
	if rawURL == "" {
		http.Error(w, "missing url query parameter", http.StatusBadRequest)
		return
	}

	parsed, err := url.Parse(rawURL)
	if err != nil || (parsed.Scheme != "http" && parsed.Scheme != "https") {
		http.Error(w, "invalid upstream url", http.StatusBadRequest)
		return
	}

	// Basic SSRF guard: allow standard media CDN hosts only
	host := strings.ToLower(parsed.Hostname())
	if !strings.HasSuffix(host, "googlevideo.com") && !strings.HasSuffix(host, "youtube.com") {
		http.Error(w, "unsupported upstream host", http.StatusForbidden)
		return
	}

	req, err := http.NewRequestWithContext(r.Context(), http.MethodGet, parsed.String(), nil)
	if err != nil {
		http.Error(w, "failed to create upstream request", http.StatusInternalServerError)
		return
	}

	if rangeHeader := r.Header.Get("Range"); rangeHeader != "" {
		req.Header.Set("Range", rangeHeader)
	}
	req.Header.Set("User-Agent", "Mozilla/5.0")

	client := &http.Client{
		Timeout: 0, // Stream until client disconnects or EOF
	}

	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, "upstream stream error", http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	for _, header := range []string{"Content-Type", "Content-Length", "Content-Range", "Accept-Ranges"} {
		if val := resp.Header.Get(header); val != "" {
			w.Header().Set(header, val)
		}
	}
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(resp.StatusCode)

	_, _ = io.Copy(w, resp.Body)
	_ = time.Now()
}
