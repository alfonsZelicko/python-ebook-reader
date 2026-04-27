import { gql } from "@apollo/client";

export const GENERATE_SPEECH_MUTATION = gql`
  mutation GenerateSpeech($input: TTSInput!, $asyncMode: Boolean!) {
    generateSpeech(input: $input, asyncMode: $asyncMode) {
      ... on TTSResultWithFile {
        success
        message
        outputFiles
        metadata {
          engineUsed
          totalChunks
          totalDurationSeconds
          outputDirectory
        }
        fileDownload {
          fileId
          filename
          downloadUrl
          contentType
          sizeBytes
        }
      }
      ... on JobCreated {
        jobId
        message
      }
    }
  }
`;

export const TRANSLATE_TEXT_MUTATION = gql`
  mutation TranslateText($input: TranslationInput!, $asyncMode: Boolean!) {
    translateText(input: $input, asyncMode: $asyncMode) {
      ... on TranslationResultWithFile {
        success
        message
        outputFile
        metadata {
          engineUsed
          sourceLanguage
          targetLanguage
          totalChunks
          outputDirectory
        }
        fileDownload {
          fileId
          filename
          downloadUrl
          contentType
          sizeBytes
        }
      }
      ... on JobCreated {
        jobId
        message
      }
    }
  }
`;
