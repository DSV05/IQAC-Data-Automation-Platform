import apiClient from "./api";
import type {
  RAGChatHistoryItem,
  RAGChatResponse,
  RAGDocumentItem,
  RAGDocumentType,
  RAGInfo,
} from "@/types";

export const ragService = {
  getInfo: async (): Promise<RAGInfo> => {
    const res = await apiClient.get("/rag/info");
    return res.data;
  },

  listDocuments: async (): Promise<RAGDocumentItem[]> => {
    const res = await apiClient.get("/rag/documents");
    return res.data;
  },

  uploadDocument: async (
    file: File,
    title: string,
    docType: RAGDocumentType,
    academicYear?: string
  ): Promise<RAGDocumentItem> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    formData.append("doc_type", docType);
    if (academicYear) formData.append("academic_year", academicYear);

    const res = await apiClient.post("/rag/documents", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  deleteDocument: async (id: string): Promise<void> => {
    await apiClient.delete(`/rag/documents/${id}`);
  },

  ask: async (question: string, documentId?: string): Promise<RAGChatResponse> => {
    const res = await apiClient.post(
      "/rag/chat",
      { question, document_id: documentId || null },
      { timeout: 180_000 } // 3 minutes — local LLMs (Ollama) can be much slower than 30s, especially with several sources
    );
    return res.data;
  },

  history: async (limit = 20): Promise<RAGChatHistoryItem[]> => {
    const res = await apiClient.get("/rag/chat/history", { params: { limit } });
    return res.data;
  },
};
