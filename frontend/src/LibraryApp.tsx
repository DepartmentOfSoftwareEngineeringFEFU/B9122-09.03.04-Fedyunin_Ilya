import { useState, useEffect } from 'react'
import { useAuth } from './context/AuthContext'

const API_BASE = 'http://127.0.0.1:8000/api/v1'

function LibraryApp() {
  const { token, user, logout } = useAuth()
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [results, setResults] = useState<any>(null)
  const [currentDocId, setCurrentDocId] = useState<number | null>(null)
  const [fileName, setFileName] = useState<string>('')
  const [method, setMethod] = useState('hybrid')
  const [annotationSentences, setAnnotationSentences] = useState(5)
  const [abstractWords, setAbstractWords] = useState(150)
  const [keywordsCount, setKeywordsCount] = useState(10)
  const [activeTab, setActiveTab] = useState<'annotation' | 'abstract' | 'keywords'>('annotation')
  const [myDocuments, setMyDocuments] = useState<any[]>([])
  const [loadingDocs, setLoadingDocs] = useState(false)

  // Загрузка документов пользователя
  const loadMyDocuments = async () => {
    if (!token) return
    setLoadingDocs(true)
    try {
      const response = await fetch(`${API_BASE}/my-documents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const docs = await response.json()
        setMyDocuments(docs)
      }
    } catch (error) {
      console.error('Ошибка загрузки документов:', error)
    } finally {
      setLoadingDocs(false)
    }
  }

  useEffect(() => {
    loadMyDocuments()
  }, [token])

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || file.type !== 'application/pdf') {
      alert('Пожалуйста, выберите PDF-файл')
      return
    }

    setFileName(file.name)
    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const uploadRes = await fetch(`${API_BASE}/upload-pdf`, {
        method: 'POST',
        body: formData,
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const uploadData = await uploadRes.json()
      setCurrentDocId(uploadData.document_id)
      alert(`Файл "${file.name}" загружен!`)
      loadMyDocuments() // Обновляем список документов
    } catch (error) {
      console.error('Ошибка загрузки:', error)
      alert('Ошибка при загрузке файла')
    } finally {
      setUploading(false)
    }
  }

  const handleProcess = async () => {
    if (!currentDocId) {
      alert('Сначала загрузите PDF-файл')
      return
    }

    setProcessing(true)
    try {
      const processRes = await fetch(
        `${API_BASE}/process/${currentDocId}?method=${method}&annotation_sentences=${annotationSentences}&abstract_words=${abstractWords}&keywords_count=${keywordsCount}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )
      const processData = await processRes.json()
      setResults(processData)
      loadMyDocuments() // Обновляем статус обработки
    } catch (error) {
      console.error('Ошибка обработки:', error)
      alert('Ошибка при обработке документа')
    } finally {
      setProcessing(false)
    }
  }

  const viewDocument = async (docId: number) => {
    try {
      const response = await fetch(`${API_BASE}/document/${docId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await response.json()
      setCurrentDocId(docId)
      setFileName(data.title)
      setResults({
        annotation: data.annotation,
        abstract: data.abstract,
        keywords: data.keywords,
        method_used: data.processing_method
      })
      setActiveTab('annotation')
    } catch (error) {
      console.error('Ошибка просмотра документа:', error)
    }
  }

  const deleteDocument = async (docId: number) => {
    if (!confirm('Удалить документ? Все результаты обработки будут потеряны.')) return

    try {
      const response = await fetch(`${API_BASE}/document/${docId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        alert('Документ удалён')
        if (currentDocId === docId) {
          setCurrentDocId(null)
          setResults(null)
          setFileName('')
        }
        loadMyDocuments()
      }
    } catch (error) {
      console.error('Ошибка удаления:', error)
    }
  }

  const getMethodName = () => {
    if (results?.method_used === 'hybrid') return 'Гибридный'
    if (results?.method_used === 'abstractive') return 'Абстрактивный'
    return 'Экстрактивный'
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    }}>
      {/* Шапка */}
      <header style={{
        background: 'white',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '20px 30px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 15 }}>
            <span style={{ fontSize: 40 }}>📚</span>
            <div>
              <h1 style={{ margin: 0, fontSize: 24, color: '#1e3a5f' }}>Научная библиотека ДВФУ</h1>
              <p style={{ margin: '5px 0 0', fontSize: 14, color: '#666' }}>Подсистема аннотирования и реферирования</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <span style={{ color: '#333' }}>👤 {user?.full_name || user?.login}</span>
            <button
              onClick={logout}
              style={{
                padding: '8px 16px',
                background: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer'
              }}
            >
              Выйти
            </button>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: 1200, margin: '30px auto', padding: '0 20px' }}>

        {/* Карточка загрузки */}
        <div style={{
          background: 'white',
          borderRadius: 20,
          padding: 30,
          marginBottom: 25,
          boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
        }}>
          <h2 style={{
            margin: '0 0 25px 0',
            fontSize: 22,
            color: '#333',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            borderBottom: '2px solid #f0f0f0',
            paddingBottom: 15,
          }}>
            <span>📄</span> Загрузка документа
          </h2>

          <div style={{ textAlign: 'center' }}>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileUpload}
              disabled={uploading}
              id="file-input"
              style={{ display: 'none' }}
            />
            <label htmlFor="file-input" style={{
              display: 'block',
              border: '2px dashed #ccc',
              borderRadius: 16,
              padding: '40px 20px',
              cursor: 'pointer',
              transition: 'all 0.3s',
              background: '#fafafa',
            }}>
              <div style={{ fontSize: 48, marginBottom: 10 }}>📁</div>
              <div style={{ fontSize: 18, fontWeight: 500, color: '#333', marginBottom: 5 }}>
                {uploading ? 'Загрузка...' : 'Нажмите для выбора PDF-файла'}
              </div>
              <div style={{ fontSize: 12, color: '#999' }}>Поддерживаются файлы в формате PDF</div>
            </label>
          </div>

          {fileName && (
            <div style={{
              marginTop: 15,
              padding: '12px 20px',
              background: '#d4edda',
              borderRadius: 10,
              color: '#155724',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}>
              <span>✅</span>
              <span>{fileName} (ID: {currentDocId})</span>
            </div>
          )}
        </div>

        {/* Карточка настроек */}
        <div style={{
          background: 'white',
          borderRadius: 20,
          padding: 30,
          marginBottom: 25,
          boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
        }}>
          <h2 style={{
            margin: '0 0 20px 0',
            fontSize: 22,
            color: '#333',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            borderBottom: '2px solid #f0f0f0',
            paddingBottom: 15,
          }}>
            <span>⚙️</span> Настройки обработки
          </h2>

          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
            marginBottom: 20,
          }}>
            <div>
              <label style={{ display: 'block', marginBottom: 8, fontWeight: 600, fontSize: 13, color: '#555' }}>
                Метод суммаризации
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  border: '1px solid #ddd',
                  borderRadius: 10,
                  fontSize: 14,
                  background: 'white',
                  color: '#333',
                }}
              >
                <option value="extractive">📌 Экстрактивный</option>
                <option value="abstractive">✨ Абстрактивный</option>
                <option value="hybrid">🔗 Гибридный</option>
              </select>
            </div>

            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 20,
              flexWrap: 'wrap',
            }}>
              <div style={{ width: 100 }}>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 12, color: '#555', textAlign: 'center' }}>
                  Аннотация
                </label>
                <input
                  type="number"
                  value={annotationSentences}
                  onChange={(e) => setAnnotationSentences(Number(e.target.value))}
                  min={1}
                  max={20}
                  style={{
                    width: '100%',
                    padding: '8px 0',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    textAlign: 'center',
                    background: '#667eea',
                    color: 'white',
                    fontWeight: 500,
                  }}
                />
                <div style={{ fontSize: 10, color: '#999', marginTop: 4, textAlign: 'center' }}>предложений</div>
              </div>

              <div style={{ width: 100 }}>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 12, color: '#555', textAlign: 'center' }}>
                  Реферат
                </label>
                <input
                  type="number"
                  value={abstractWords}
                  onChange={(e) => setAbstractWords(Number(e.target.value))}
                  min={30}
                  max={600}
                  style={{
                    width: '100%',
                    padding: '8px 0',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    textAlign: 'center',
                    background: '#667eea',
                    color: 'white',
                    fontWeight: 500,
                  }}
                />
                <div style={{ fontSize: 10, color: '#999', marginTop: 4, textAlign: 'center' }}>слов</div>
              </div>

              <div style={{ width: 100 }}>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 12, color: '#555', textAlign: 'center' }}>
                  Ключевые слова
                </label>
                <input
                  type="number"
                  value={keywordsCount}
                  onChange={(e) => setKeywordsCount(Number(e.target.value))}
                  min={3}
                  max={30}
                  style={{
                    width: '100%',
                    padding: '8px 0',
                    border: 'none',
                    borderRadius: 8,
                    fontSize: 14,
                    textAlign: 'center',
                    background: '#667eea',
                    color: 'white',
                    fontWeight: 500,
                  }}
                />
                <div style={{ fontSize: 10, color: '#999', marginTop: 4, textAlign: 'center' }}>фраз</div>
              </div>
            </div>
          </div>

          <button
            onClick={handleProcess}
            disabled={processing || !currentDocId}
            style={{
              width: '100%',
              padding: '12px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: 10,
              fontSize: 14,
              fontWeight: 600,
              cursor: processing || !currentDocId ? 'not-allowed' : 'pointer',
              opacity: processing || !currentDocId ? 0.6 : 1,
            }}
          >
            {processing ? '⏳ Обработка документа...' : '🚀 Сформировать аннотацию и реферат'}
          </button>
        </div>

        {/* Результаты */}
        {results && (
          <div style={{
            background: 'white',
            borderRadius: 20,
            padding: 30,
            boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
            marginBottom: 25,
          }}>
            <h2 style={{
              margin: '0 0 20px 0',
              fontSize: 22,
              color: '#333',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              borderBottom: '2px solid #f0f0f0',
              paddingBottom: 15,
            }}>
              <span>📖</span> Результаты обработки
              <span style={{
                marginLeft: 'auto',
                fontSize: 11,
                padding: '2px 10px',
                background: '#e8f0fe',
                borderRadius: 20,
                color: '#667eea',
              }}>{getMethodName()}</span>
            </h2>

            <div style={{
              display: 'flex',
              gap: 8,
              borderBottom: '2px solid #f0f0f0',
              marginBottom: 20,
            }}>
              <button
                onClick={() => setActiveTab('annotation')}
                style={{
                  padding: '8px 20px',
                  background: activeTab === 'annotation' ? '#f5f7ff' : 'none',
                  border: 'none',
                  fontSize: 14,
                  fontWeight: activeTab === 'annotation' ? 600 : 500,
                  color: activeTab === 'annotation' ? '#667eea' : '#666',
                  cursor: 'pointer',
                  borderRadius: '10px 10px 0 0',
                  borderBottom: activeTab === 'annotation' ? '3px solid #667eea' : 'none',
                }}
              >
                📝 Аннотация
              </button>
              <button
                onClick={() => setActiveTab('abstract')}
                style={{
                  padding: '8px 20px',
                  background: activeTab === 'abstract' ? '#f5f7ff' : 'none',
                  border: 'none',
                  fontSize: 14,
                  fontWeight: activeTab === 'abstract' ? 600 : 500,
                  color: activeTab === 'abstract' ? '#667eea' : '#666',
                  cursor: 'pointer',
                  borderRadius: '10px 10px 0 0',
                  borderBottom: activeTab === 'abstract' ? '3px solid #667eea' : 'none',
                }}
              >
                📑 Реферат
              </button>
              <button
                onClick={() => setActiveTab('keywords')}
                style={{
                  padding: '8px 20px',
                  background: activeTab === 'keywords' ? '#f5f7ff' : 'none',
                  border: 'none',
                  fontSize: 14,
                  fontWeight: activeTab === 'keywords' ? 600 : 500,
                  color: activeTab === 'keywords' ? '#667eea' : '#666',
                  cursor: 'pointer',
                  borderRadius: '10px 10px 0 0',
                  borderBottom: activeTab === 'keywords' ? '3px solid #667eea' : 'none',
                }}
              >
                🏷️ Ключевые слова
              </button>
            </div>

            <div>
              {activeTab === 'annotation' && (
                <div style={{
                  background: '#f8f9fa',
                  padding: 20,
                  borderRadius: 12,
                  fontSize: 14,
                  lineHeight: 1.5,
                  color: '#333',
                  maxHeight: 350,
                  overflowY: 'auto',
                }}>
                  {results.annotation || 'Аннотация не сформирована'}
                </div>
              )}
              {activeTab === 'abstract' && (
                <div style={{
                  background: '#f8f9fa',
                  padding: 20,
                  borderRadius: 12,
                  fontSize: 14,
                  lineHeight: 1.5,
                  color: '#333',
                  maxHeight: 350,
                  overflowY: 'auto',
                }}>
                  {results.abstract || 'Реферат не сформирован'}
                </div>
              )}
              {activeTab === 'keywords' && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                  {results.keywords?.map((kw: string, idx: number) => (
                    <span key={idx} style={{
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                      padding: '6px 14px',
                      borderRadius: 20,
                      fontSize: 13,
                    }}>
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Мои документы */}
        <div style={{
          background: 'white',
          borderRadius: 20,
          padding: 30,
          boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
        }}>
          <h2 style={{
            margin: '0 0 20px 0',
            fontSize: 22,
            color: '#333',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            borderBottom: '2px solid #f0f0f0',
            paddingBottom: 15,
          }}>
            <span>📋</span> Мои документы
            <button
              onClick={loadMyDocuments}
              style={{
                marginLeft: 'auto',
                padding: '5px 12px',
                background: '#e0e0e0',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
                fontSize: 12
              }}
            >
              🔄 Обновить
            </button>
          </h2>

          {loadingDocs ? (
            <p>Загрузка...</p>
          ) : myDocuments.length === 0 ? (
            <p style={{ color: '#999', textAlign: 'center', padding: 40 }}>
              Нет загруженных документов. Загрузите первый PDF-файл выше.
            </p>
          ) : (
            <div style={{ display: 'grid', gap: 10 }}>
              {myDocuments.map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '12px 16px',
                    background: '#f8f9fa',
                    borderRadius: 12,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onClick={() => viewDocument(doc.id)}
                >
                  <div>
                    <div style={{ fontWeight: 500 }}>{doc.title}</div>
                    <div style={{ fontSize: 12, color: '#666' }}>
                      ID: {doc.id} | Загружен: {new Date(doc.created_at).toLocaleDateString()}
                      {doc.has_processing && <span style={{ marginLeft: 10, color: '#10b981' }}>✅ Обработан</span>}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteDocument(doc.id)
                    }}
                    style={{
                      padding: '6px 12px',
                      background: '#fee2e2',
                      color: '#dc2626',
                      border: 'none',
                      borderRadius: 8,
                      cursor: 'pointer',
                      fontSize: 12
                    }}
                  >
                    🗑️ Удалить
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <footer style={{
        textAlign: 'center',
        padding: '20px',
        color: 'rgba(255,255,255,0.7)',
        fontSize: 12,
      }}>
        <p>© 2026 Научная библиотека Дальневосточного федерального университета</p>
      </footer>
    </div>
  )
}

export default LibraryApp