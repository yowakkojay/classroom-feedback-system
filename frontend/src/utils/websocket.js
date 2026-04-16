export function createWebSocket(path, onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const token = sessionStorage.getItem('access_token')
  const url = `${protocol}//${window.location.host}${path}?token=${token}`
  const ws = new WebSocket(url)

  ws.onopen = () => {
    console.log('WebSocket connected:', path)
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    onMessage(data)
  }

  ws.onclose = () => {
    console.log('WebSocket disconnected:', path)
    // Auto reconnect after 3 seconds
    setTimeout(() => {
      createWebSocket(path, onMessage)
    }, 3000)
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }

  return ws
}
