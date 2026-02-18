"""Tests for topic segmentation."""
import pytest
from mcp_youtube_intelligence.core.segmenter import segment_topics, MIN_SEGMENT_CHARS


class TestSegmentTopics:
    def test_empty_string(self):
        assert segment_topics("") == []

    def test_no_markers(self):
        text = "This is a normal paragraph without any topic transitions."
        result = segment_topics(text)
        assert len(result) == 1
        assert result[0]["segment"] == 0
        assert result[0]["text"] == text

    def test_korean_marker_splits(self):
        text = "첫 번째 내용입니다. 다음 주제로 넘어가겠습니다. 두 번째 내용입니다."
        result = segment_topics(text)
        assert len(result) >= 1

    def test_english_marker_splits(self):
        text = ("Introduction to the course and some lengthy initial content that fills space and provides background context for everything we will cover today in this session. "
                "Moving on to the next topic, we discuss AI and its applications in detail across many industries and use cases that are transforming the modern world.")
        result = segment_topics(text)
        assert len(result) >= 2

    def test_segment_indices_sequential(self):
        text = "Part one with enough content to be a real segment here. Next topic is here with detailed explanation. Let's talk about something else entirely. Moving on to finale and wrapping up."
        result = segment_topics(text)
        for i, seg in enumerate(result):
            assert seg["segment"] == i

    def test_char_count_matches(self):
        text = "Hello world without any markers at all."
        result = segment_topics(text)
        assert result[0]["char_count"] == len(result[0]["text"])

    def test_multiple_korean_markers(self):
        text = ("오늘의 첫 번째 주제는 경제입니다. 많은 변화가 있었고 여러 분야에서 성장이 이어졌습니다. 특히 글로벌 경제는 큰 변동을 보이고 있으며 각국의 정책이 중요한 역할을 하고 있습니다. "
                "다음 주제는 기술입니다. 기술 발전이 빠르며 AI 분야가 특히 주목받고 있습니다. 반도체 산업도 큰 성장을 보이며 글로벌 공급망이 재편되고 있습니다. "
                "마지막 주제는 문화입니다. 다양한 문화 콘텐츠가 세계적으로 인기를 끌고 있으며 한류의 영향력이 점점 커지고 있습니다.")
        result = segment_topics(text)
        assert len(result) >= 2

    def test_lets_talk_about_marker(self):
        text = ("Some intro content here with enough detail to fill a segment properly and give us context about the broader landscape of technology and innovation in this field. "
                "Let's talk about machine learning now. It is fascinating and has many applications across industries including healthcare, finance, and autonomous vehicles.")
        result = segment_topics(text)
        assert len(result) >= 2

    def test_mid_sentence_no_false_positive(self):
        """'next thing' mid-sentence should NOT trigger segmentation."""
        text = "The next thing in the code is a function call that does processing. We also handle errors gracefully in this module."
        result = segment_topics(text)
        assert len(result) == 1

    def test_sentence_start_marker_matches(self):
        """Marker at sentence start should trigger segmentation."""
        text = ("We covered basics above with plenty of detail for context and background information that helps set the stage for our deeper discussion. "
                "Next topic is advanced patterns that build on the fundamentals we discussed and extend them into practical real-world applications and use cases.")
        result = segment_topics(text)
        assert len(result) >= 2

    def test_small_segment_merged(self):
        """Segments smaller than MIN_SEGMENT_CHARS should merge into previous."""
        text = ("A very long introduction segment that has plenty of content to be valid on its own and provides detailed context. "
                "다음 주제는 짧다. "
                "마지막 주제는 이것으로 마무리하며 충분히 긴 내용을 포함하고 있습니다 자세한 설명과 함께 여러 가지 포인트를 다루겠습니다.")
        result = segment_topics(text)
        for seg in result:
            assert seg["char_count"] >= MIN_SEGMENT_CHARS or len(result) == 1

    def test_all_segments_above_minimum(self):
        """All resulting segments should be >= MIN_SEGMENT_CHARS (unless only 1 segment)."""
        text = ("Introduction with substantial content here for the first part of our discussion. "
                "Next topic covers AI and machine learning with detailed explanations and examples. "
                "Moving on to cloud computing infrastructure and deployment strategies in production.")
        result = segment_topics(text)
        if len(result) > 1:
            for seg in result:
                assert seg["char_count"] >= MIN_SEGMENT_CHARS

    # --- New tests for enhanced segmenter ---

    def test_long_text_no_markers_splits(self):
        """Long text (1000+ words) without markers should produce multiple segments."""
        # Generate ~1200 words of marker-free text
        sentences = []
        topics = [
            "Machine learning algorithms process data to find patterns and make predictions. ",
            "Neural networks consist of layers of interconnected nodes that transform inputs. ",
            "Training involves adjusting weights through backpropagation and gradient descent. ",
            "Convolutional networks excel at image recognition and computer vision tasks. ",
            "Recurrent networks handle sequential data like text and time series effectively. ",
            "Transfer learning allows models pretrained on large datasets to be fine-tuned. ",
            "Data preprocessing includes normalization scaling and feature engineering steps. ",
            "Overfitting occurs when a model memorizes training data instead of generalizing. ",
            "Regularization techniques like dropout and weight decay prevent overfitting issues. ",
            "Hyperparameter tuning optimizes learning rate batch size and architecture choices. ",
        ]
        # Repeat to get 1000+ words
        for _ in range(15):
            sentences.extend(topics)
        text = " ".join(sentences)

        word_count = len(text.split())
        assert word_count > 1000, f"Test text should be >1000 words, got {word_count}"

        result = segment_topics(text)
        assert len(result) >= 2, f"Expected >=2 segments for {word_count}-word text, got {len(result)}"

    def test_topic_label_present(self):
        """Each segment should have a 'topic' key with keyword labels."""
        text = ("Machine learning and artificial intelligence are transforming industries worldwide. "
                "Next topic is about cloud computing and distributed systems architecture.")
        result = segment_topics(text)
        for seg in result:
            assert "topic" in seg
            # At least the longer segments should have non-empty topic
            if seg["char_count"] > 50:
                assert seg["topic"], f"Expected non-empty topic for segment: {seg['text'][:50]}"

    def test_korean_marker_다음으로(self):
        """한국어 '다음으로' 마커가 분할을 트리거해야 합니다."""
        text = ("인공지능의 기본 개념에 대해 알아보았습니다. 머신러닝과 딥러닝의 차이점을 이해하는 것이 중요합니다. 지도학습과 비지도학습 그리고 강화학습의 차이도 살펴보았습니다. "
                "다음으로 자연어 처리에 대해 살펴보겠습니다. 자연어 처리는 컴퓨터가 인간의 언어를 이해하고 생성하는 기술입니다. 최근에는 대규모 언어 모델이 큰 발전을 이루고 있습니다.")
        result = segment_topics(text)
        assert len(result) >= 2, f"Expected >=2 segments with '다음으로' marker, got {len(result)}"

    def test_english_summary_marker(self):
        """'In summary' and 'To conclude' should trigger segmentation."""
        text = ("We have discussed many important points about renewable energy sources and their environmental impact on global climate change and sustainability efforts worldwide. "
                "In summary, the transition to clean energy is both necessary and economically viable for developed and developing nations alike in the coming decades.")
        result = segment_topics(text)
        assert len(result) >= 2

    def test_to_conclude_marker(self):
        """'To conclude' marker test."""
        text = ("The research findings show significant improvements in treatment outcomes across multiple clinical trials conducted over the past five years in major medical centers. "
                "To conclude, this new approach offers promising results that warrant further investigation and larger scale randomized controlled trials.")
        result = segment_topics(text)
        assert len(result) >= 2

    def test_keyword_extraction_quality(self):
        """Keywords should reflect the actual content, not be stopwords."""
        text = "Python programming language is excellent for data science and machine learning applications. Python provides libraries like pandas numpy and scikit-learn for analysis."
        result = segment_topics(text)
        assert len(result) == 1
        topic = result[0]["topic"]
        assert topic  # non-empty
        # Should contain meaningful words
        keywords = [k.strip() for k in topic.split(",")]
        stopwords = {"the", "a", "is", "and", "for", "to", "of"}
        for kw in keywords:
            assert kw.lower() not in stopwords

    def test_min_segment_chars(self):
        """MIN_SEGMENT_CHARS should be 60."""
        assert MIN_SEGMENT_CHARS == 60
