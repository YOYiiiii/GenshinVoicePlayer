using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace VoicePlayer
{
    public class CharIndex
    {
        [JsonPropertyName("id")] public string Id { get; set; }
        [JsonPropertyName("name")] public string Name { get; set; }
        [JsonPropertyName("order")] public long Order { get; set; }
        [JsonPropertyName("total")] public int Total { get; set; }
        [JsonPropertyName("vocal")] public int Vocal { get; set; }
        [JsonPropertyName("cats")] public Dictionary<string, int> Cats { get; set; }
        [JsonPropertyName("group")] public string Group { get; set; }
    }

    public class Track
    {
        [JsonPropertyName("name")] public string Name { get; set; }
        [JsonPropertyName("pck")] public string Pck { get; set; }
        [JsonPropertyName("id")] public string Id { get; set; }
    }

    public class MusicGroup
    {
        [JsonPropertyName("group")] public string Group { get; set; }
        [JsonPropertyName("bg")] public string Bg { get; set; }
        [JsonPropertyName("bg_blur")] public string BgBlur { get; set; }
        [JsonPropertyName("tracks")] public List<Track> Tracks { get; set; }
    }

    public class IndexData
    {
        [JsonPropertyName("characters")] public List<CharIndex> Characters { get; set; }
        [JsonPropertyName("music")] public List<MusicGroup> Music { get; set; }
    }

    public class CatGroup
    {
        [JsonPropertyName("key")] public string Key { get; set; }
        [JsonPropertyName("label")] public string Label { get; set; }
        [JsonPropertyName("items")] public List<string[]> Items { get; set; }
    }

    public class EntryDetail
    {
        [JsonPropertyName("id")] public string Id { get; set; }
        [JsonPropertyName("name")] public string Name { get; set; }
        [JsonPropertyName("bg")] public string Bg { get; set; }
        [JsonPropertyName("bg_blur")] public string BgBlur { get; set; }
        [JsonPropertyName("categories")] public List<CatGroup> Categories { get; set; }
    }
}
