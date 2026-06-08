/**
 * 来源：新建 XLSX 工作表.xlsx（火山 1.0 音色清单）
 */

export interface TtsVoiceOption {
  scene: string;
  label: string;
  value: string;
  language: string;
  capabilities: string;
  tags?: string;
  description: string;
}

export const HUOSHAN_TTS_VOICE_OPTIONS: TtsVoiceOption[] = [
  {
    "scene": "多情感",
    "label": "冷酷哥哥（多情感）",
    "value": "zh_male_lengkugege_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "生气、冷漠、恐惧、开心、厌恶、中性、悲伤、沮丧",
    "description": "语种/方言：中文；支持情感：生气、冷漠、恐惧、开心、厌恶、中性、悲伤、沮丧；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "甜心小美（多情感）",
    "value": "zh_female_tianxinxiaomei_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "悲伤、恐惧、厌恶、中性",
    "description": "语种/方言：中文；支持情感：悲伤、恐惧、厌恶、中性；标签：剪映同款；MIX：否",
    "tags": "剪映同款"
  },
  {
    "scene": "多情感",
    "label": "高冷御姐（多情感）",
    "value": "zh_female_gaolengyujie_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "开心、悲伤、生气、惊讶、恐惧、厌恶、激动、冷漠、中性",
    "description": "语种/方言：中文；支持情感：开心、悲伤、生气、惊讶、恐惧、厌恶、激动、冷漠、中性；标签：剪映同款；对应2.0：高冷御姐 2.0；MIX：否",
    "tags": "剪映同款"
  },
  {
    "scene": "多情感",
    "label": "傲娇霸总（多情感）",
    "value": "zh_male_aojiaobazong_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "中性、开心、愤怒、厌恶",
    "description": "语种/方言：中文；支持情感：中性、开心、愤怒、厌恶；标签：剪映同款；对应2.0：傲娇霸总 2.0；MIX：否",
    "tags": "剪映同款"
  },
  {
    "scene": "多情感",
    "label": "广州德哥（多情感）",
    "value": "zh_male_guangzhoudege_emo_mars_bigtts",
    "language": "中文",
    "capabilities": "生气、恐惧、中性",
    "description": "语种/方言：中文；支持情感：生气、恐惧、中性；标签：剪映同款；MIX：是",
    "tags": "剪映同款"
  },
  {
    "scene": "多情感",
    "label": "京腔侃爷（多情感）",
    "value": "zh_male_jingqiangkanye_emo_mars_bigtts",
    "language": "中文",
    "capabilities": "开心、生气、惊讶、厌恶、中性",
    "description": "语种/方言：中文；支持情感：开心、生气、惊讶、厌恶、中性；标签：剪映同款；MIX：是",
    "tags": "剪映同款"
  },
  {
    "scene": "多情感",
    "label": "邻居阿姨（多情感）",
    "value": "zh_female_linjuayi_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "中性、愤怒、冷漠、沮丧、惊讶",
    "description": "语种/方言：中文；支持情感：中性、愤怒、冷漠、沮丧、惊讶；标签：剪映同款；MIX：否",
    "tags": "剪映同款"
  },
  {
    "scene": "多情感",
    "label": "优柔公子（多情感）",
    "value": "zh_male_yourougongzi_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "开心、生气、恐惧、厌恶、激动、中性、沮丧",
    "description": "语种/方言：中文；支持情感：开心、生气、恐惧、厌恶、激动、中性、沮丧；标签：剪映同款；MIX：否",
    "tags": "剪映同款"
  },
  {
    "scene": "多情感",
    "label": "儒雅男友（多情感）",
    "value": "zh_male_ruyayichen_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "开心、悲伤、生气、恐惧、激动、冷漠、中性",
    "description": "语种/方言：中文；支持情感：开心、悲伤、生气、恐惧、激动、冷漠、中性；标签：剪映同款；MIX：否",
    "tags": "剪映同款"
  },
  {
    "scene": "多情感",
    "label": "俊朗男友（多情感）",
    "value": "zh_male_junlangnanyou_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "开心、悲伤、生气、惊讶、恐惧、中性",
    "description": "语种/方言：中文；支持情感：开心、悲伤、生气、惊讶、恐惧、中性；标签：剪映同款；MIX：否",
    "tags": "剪映同款"
  },
  {
    "scene": "多情感",
    "label": "北京小爷（多情感）",
    "value": "zh_male_beijingxiaoye_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "生气，惊讶，恐惧，激动，冷漠，中性",
    "description": "语种/方言：中文；支持情感：生气，惊讶，恐惧，激动，冷漠，中性；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "柔美女友（多情感）",
    "value": "zh_female_roumeinvyou_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "开心，悲伤，生气，惊讶，恐惧，厌恶，激动，冷漠，中性",
    "description": "语种/方言：中文；支持情感：开心，悲伤，生气，惊讶，恐惧，厌恶，激动，冷漠，中性；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "阳光青年（多情感）",
    "value": "zh_male_yangguangqingnian_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "开心，悲伤，生气，恐惧，激动，冷漠，中性",
    "description": "语种/方言：中文；支持情感：开心，悲伤，生气，恐惧，激动，冷漠，中性；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "魅力女友（多情感）",
    "value": "zh_female_meilinvyou_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "悲伤，恐惧，中性",
    "description": "语种/方言：中文；支持情感：悲伤，恐惧，中性；对应2.0：魅力女友 2.0；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "爽快思思（多情感）",
    "value": "zh_female_shuangkuaisisi_emo_v2_mars_bigtts",
    "language": "中文,英式英语",
    "capabilities": "开心，悲伤，生气，惊讶，激动，冷漠，中性",
    "description": "语种/方言：中文,英式英语；支持情感：开心，悲伤，生气，惊讶，激动，冷漠，中性；对应2.0：爽快思思 2.0；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "Candice",
    "value": "en_female_candice_emo_v2_mars_bigtts",
    "language": "美式英语",
    "capabilities": "深情、愤怒、ASMR、对话/闲聊、兴奋、愉悦、中性、温暖",
    "description": "语种/方言：美式英语；支持情感：深情、愤怒、ASMR、对话/闲聊、兴奋、愉悦、中性、温暖；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "Serena",
    "value": "en_female_skye_emo_v2_mars_bigtts",
    "language": "美式英语",
    "capabilities": "深情、愤怒、ASMR、对话/闲聊、兴奋、愉悦、中性、悲伤、温暖",
    "description": "语种/方言：美式英语；支持情感：深情、愤怒、ASMR、对话/闲聊、兴奋、愉悦、中性、悲伤、温暖；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "Glen",
    "value": "en_male_glen_emo_v2_mars_bigtts",
    "language": "美式英语",
    "capabilities": "深情、愤怒、ASMR、对话/闲聊、深情、兴奋、愉悦、中性、悲伤、温暖",
    "description": "语种/方言：美式英语；支持情感：深情、愤怒、ASMR、对话/闲聊、深情、兴奋、愉悦、中性、悲伤、温暖；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "Sylus",
    "value": "en_male_sylus_emo_v2_mars_bigtts",
    "language": "美式英语",
    "capabilities": "深情、愤怒、ASMR、权威、对话/闲聊、兴奋、愉悦、中性、悲伤、温暖",
    "description": "语种/方言：美式英语；支持情感：深情、愤怒、ASMR、权威、对话/闲聊、兴奋、愉悦、中性、悲伤、温暖；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "Corey",
    "value": "en_male_corey_emo_v2_mars_bigtts",
    "language": "英式英语",
    "capabilities": "愤怒、ASMR、权威、对话/闲聊、深情、兴奋、愉悦、中性、悲伤、温暖",
    "description": "语种/方言：英式英语；支持情感：愤怒、ASMR、权威、对话/闲聊、深情、兴奋、愉悦、中性、悲伤、温暖；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "Nadia",
    "value": "en_female_nadia_tips_emo_v2_mars_bigtts",
    "language": "英式英语",
    "capabilities": "深情、愤怒、ASMR、对话/闲聊、深情、兴奋、愉悦、中性、悲伤、温暖",
    "description": "语种/方言：英式英语；支持情感：深情、愤怒、ASMR、对话/闲聊、深情、兴奋、愉悦、中性、悲伤、温暖；MIX：否"
  },
  {
    "scene": "多情感",
    "label": "深夜播客",
    "value": "zh_male_shenyeboke_emo_v2_mars_bigtts",
    "language": "中文",
    "capabilities": "惊讶、悲伤、中性、厌恶、开心、恐惧、激动、沮丧、冷漠、生气",
    "description": "语种/方言：中文；支持情感：惊讶、悲伤、中性、厌恶、开心、恐惧、激动、沮丧、冷漠、生气；标签：猫箱同款；对应2.0：深夜播客 2.0；MIX：否",
    "tags": "猫箱同款"
  },
  {
    "scene": "教育场景",
    "label": "Tina老师",
    "value": "zh_female_yingyujiaoyu_mars_bigtts",
    "language": "中文,英式英语",
    "capabilities": "",
    "description": "语种/方言：中文,英式英语；对应2.0：Tina老师 2.0；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "温柔女神",
    "value": "ICL_zh_female_wenrounvshen_239eff5e8ffa_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "Vivi",
    "value": "zh_female_vv_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：Vivi 2.0；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "亲切女声",
    "value": "zh_female_qinqienvsheng_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：亲切女声 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "机灵小伙",
    "value": "ICL_zh_male_shenmi_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "元气甜妹",
    "value": "ICL_zh_female_wuxi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "知心姐姐",
    "value": "ICL_zh_female_wenyinvsheng_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "阳光阿辰",
    "value": "zh_male_qingyiyuxuan_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "快乐小东",
    "value": "zh_male_xudong_conversation_wvae_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：快乐小东 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "冷酷哥哥",
    "value": "ICL_zh_male_lengkugege_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "纯澈女生",
    "value": "ICL_zh_female_feicui_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "初恋女友",
    "value": "ICL_zh_female_yuxin_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "贴心闺蜜",
    "value": "ICL_zh_female_xnx_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "温柔白月光",
    "value": "ICL_zh_female_yry_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "炀炀",
    "value": "ICL_zh_male_BV705_streaming_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "开朗学长",
    "value": "en_male_jason_conversation_wvae_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：开朗学长 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "魅力苏菲",
    "value": "zh_female_sophie_conversation_wvae_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：魅力苏菲 2.0；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "贴心妹妹",
    "value": "ICL_zh_female_yilin_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "甜美桃子",
    "value": "zh_female_tianmeitaozi_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：甜美桃子 2.0；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "清新女声",
    "value": "zh_female_qingxinnvsheng_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：清新女声 2.0；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "知性女声",
    "value": "zh_female_zhixingnvsheng_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：知性女声 2.0；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "清爽男大",
    "value": "zh_male_qingshuangnanda_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：清爽男大 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "邻家女孩",
    "value": "zh_female_linjianvhai_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：邻家女孩 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "渊博小叔",
    "value": "zh_male_yuanboxiaoshu_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、剪映同款；对应2.0：渊博小叔 2.0；MIX：是",
    "tags": "豆包同款、剪映同款"
  },
  {
    "scene": "通用场景",
    "label": "阳光青年",
    "value": "zh_male_yangguangqingnian_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：阳光青年 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "甜美小源",
    "value": "zh_female_tianmeixiaoyuan_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：甜美小源 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "清澈梓梓",
    "value": "zh_female_qingchezizi_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：清澈梓梓 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "解说小明",
    "value": "zh_male_jieshuoxiaoming_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：解说小明 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "开朗姐姐",
    "value": "zh_female_kailangjiejie_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：开朗姐姐 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "邻家男孩",
    "value": "zh_male_linjiananhai_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：邻家男孩 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "甜美悦悦",
    "value": "zh_female_tianmeiyueyue_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：甜美悦悦 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "心灵鸡汤",
    "value": "zh_female_xinlingjitang_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：心灵鸡汤 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "知性温婉",
    "value": "ICL_zh_female_zhixingwenwan_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "通用场景",
    "label": "暖心体贴",
    "value": "ICL_zh_male_nuanxintitie_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "通用场景",
    "label": "开朗轻快",
    "value": "ICL_zh_male_kailangqingkuai_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "通用场景",
    "label": "活泼爽朗",
    "value": "ICL_zh_male_huoposhuanglang_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "通用场景",
    "label": "率真小伙",
    "value": "ICL_zh_male_shuaizhenxiaohuo_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "通用场景",
    "label": "温柔小哥",
    "value": "zh_male_wenrouxiaoge_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：温柔小哥 2.0；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "灿灿/Shiny",
    "value": "zh_female_cancan_mars_bigtts",
    "language": "中文,美式英语",
    "capabilities": "",
    "description": "语种/方言：中文,美式英语；对应2.0：知性灿灿 2.0；MIX：是"
  },
  {
    "scene": "通用场景",
    "label": "爽快思思/Skye",
    "value": "zh_female_shuangkuaisisi_moon_bigtts",
    "language": "中文,美式英语",
    "capabilities": "",
    "description": "语种/方言：中文,美式英语；标签：豆包同款；对应2.0：爽快思思 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "温暖阿虎/Alvin",
    "value": "zh_male_wennuanahu_moon_bigtts",
    "language": "中文,美式英语",
    "capabilities": "",
    "description": "语种/方言：中文,美式英语；标签：豆包同款；对应2.0：温暖阿虎/Alvin 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "通用场景",
    "label": "少年梓辛/Brayan",
    "value": "zh_male_shaonianzixin_moon_bigtts",
    "language": "中文,美式英语",
    "capabilities": "",
    "description": "语种/方言：中文,美式英语；标签：豆包同款、剪映同款；对应2.0：少年梓辛/Brayan 2.0；MIX：是",
    "tags": "豆包同款、剪映同款"
  },
  {
    "scene": "通用场景、S2S-SC",
    "label": "温柔文雅",
    "value": "ICL_zh_female_wenrouwenya_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "IP仿音",
    "label": "沪普男",
    "value": "zh_male_hupunan_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "IP仿音",
    "label": "鲁班七号",
    "value": "zh_male_lubanqihao_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：抖音同款、剪映同款、豆包同款；对应2.0：鲁班七号 2.0；MIX：是",
    "tags": "抖音同款、剪映同款、豆包同款"
  },
  {
    "scene": "IP仿音",
    "label": "林潇",
    "value": "zh_female_yangmi_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、抖音同款、豆包同款；对应2.0：林潇 2.0；MIX：是",
    "tags": "剪映同款、抖音同款、豆包同款"
  },
  {
    "scene": "IP仿音",
    "label": "玲玲姐姐",
    "value": "zh_female_linzhiling_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、抖音同款、豆包同款；对应2.0：玲玲姐姐 2.0；MIX：是",
    "tags": "剪映同款、抖音同款、豆包同款"
  },
  {
    "scene": "IP仿音",
    "label": "春日部姐姐",
    "value": "zh_female_jiyejizi2_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：抖音同款、剪映同款、豆包同款；对应2.0：春日部姐姐 2.0；MIX：是",
    "tags": "抖音同款、剪映同款、豆包同款"
  },
  {
    "scene": "IP仿音",
    "label": "唐僧",
    "value": "zh_male_tangseng_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：抖音同款、豆包同款；对应2.0：唐僧 2.0；MIX：是",
    "tags": "抖音同款、豆包同款"
  },
  {
    "scene": "IP仿音",
    "label": "庄周",
    "value": "zh_male_zhuangzhou_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、抖音同款；对应2.0：庄周 2.0；MIX：是",
    "tags": "剪映同款、抖音同款"
  },
  {
    "scene": "IP仿音",
    "label": "猪八戒",
    "value": "zh_male_zhubajie_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、豆包同款；对应2.0：猪八戒 2.0；MIX：是",
    "tags": "剪映同款、豆包同款"
  },
  {
    "scene": "IP仿音",
    "label": "感冒电音姐姐",
    "value": "zh_female_ganmaodianyin_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、抖音同款；对应2.0：感冒电音姐姐 2.0；MIX：是",
    "tags": "剪映同款、抖音同款"
  },
  {
    "scene": "IP仿音",
    "label": "直率英子",
    "value": "zh_female_naying_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、抖音同款、豆包同款；对应2.0：直率英子 2.0；MIX：是",
    "tags": "剪映同款、抖音同款、豆包同款"
  },
  {
    "scene": "IP仿音",
    "label": "女雷神",
    "value": "zh_female_leidian_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、豆包同款；对应2.0：女雷神 2.0；MIX：是",
    "tags": "剪映同款、豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "粤语小溏",
    "value": "zh_female_yueyunv_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "趣味口音",
    "label": "豫州子轩",
    "value": "zh_male_yuzhouzixuan_moon_bigtts",
    "language": "中文-河南口音",
    "capabilities": "",
    "description": "语种/方言：中文-河南口音；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "呆萌川妹",
    "value": "zh_female_daimengchuanmei_moon_bigtts",
    "language": "中文-四川口音",
    "capabilities": "",
    "description": "语种/方言：中文-四川口音；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "广西远舟",
    "value": "zh_male_guangxiyuanzhou_moon_bigtts",
    "language": "中文-广西口音",
    "capabilities": "",
    "description": "语种/方言：中文-广西口音；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "双节棍小哥",
    "value": "zh_male_zhoujielun_emo_v2_mars_bigtts",
    "language": "中文-台湾口音",
    "capabilities": "",
    "description": "语种/方言：中文-台湾口音；标签：抖音同款、剪映同款、豆包同款；MIX：否",
    "tags": "抖音同款、剪映同款、豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "湾湾小何",
    "value": "zh_female_wanwanxiaohe_moon_bigtts",
    "language": "中文-台湾口音",
    "capabilities": "",
    "description": "语种/方言：中文-台湾口音；标签：豆包同款；对应2.0：小何 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "湾区大叔",
    "value": "zh_female_wanqudashu_moon_bigtts",
    "language": "中文-广东口音",
    "capabilities": "",
    "description": "语种/方言：中文-广东口音；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "广州德哥",
    "value": "zh_male_guozhoudege_moon_bigtts",
    "language": "中文-广东口音",
    "capabilities": "",
    "description": "语种/方言：中文-广东口音；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "浩宇小哥",
    "value": "zh_male_haoyuxiaoge_moon_bigtts",
    "language": "中文-青岛口音",
    "capabilities": "",
    "description": "语种/方言：中文-青岛口音；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "北京小爷",
    "value": "zh_male_beijingxiaoye_moon_bigtts",
    "language": "中文-北京口音",
    "capabilities": "",
    "description": "语种/方言：中文-北京口音；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "京腔侃爷/Harmony",
    "value": "zh_male_jingqiangkanye_moon_bigtts",
    "language": "中文-北京口音,美式英语",
    "capabilities": "",
    "description": "语种/方言：中文-北京口音,美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "趣味口音",
    "label": "妹坨洁儿",
    "value": "zh_female_meituojieer_moon_bigtts",
    "language": "中文-长沙口音",
    "capabilities": "",
    "description": "语种/方言：中文-长沙口音；标签：豆包同款、剪映同款；MIX：是",
    "tags": "豆包同款、剪映同款"
  },
  {
    "scene": "角色扮演",
    "label": "纯真少女",
    "value": "ICL_zh_female_chunzhenshaonv_e588402fb8ad_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "奶气小生",
    "value": "ICL_zh_male_xiaonaigou_edf58cf28b8b_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "精灵向导",
    "value": "ICL_zh_female_jinglingxiangdao_1beb294a9e3e_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "闷油瓶小哥",
    "value": "ICL_zh_male_menyoupingxiaoge_ffed9fc2fee7_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "黯刃秦主",
    "value": "ICL_zh_male_anrenqinzhu_cd62e63dcdab_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "霸道总裁",
    "value": "ICL_zh_male_badaozongcai_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "妩媚可人",
    "value": "ICL_zh_female_ganli_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "邪魅御姐",
    "value": "ICL_zh_female_xiangliangya_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "嚣张小哥",
    "value": "ICL_zh_male_ms_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "油腻大叔",
    "value": "ICL_zh_male_you_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "孤傲公子",
    "value": "ICL_zh_male_guaogongzi_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "胡子叔叔",
    "value": "ICL_zh_male_huzi_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "性感魅惑",
    "value": "ICL_zh_female_luoqing_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "病弱公子",
    "value": "ICL_zh_male_bingruogongzi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "邪魅女王",
    "value": "ICL_zh_female_bingjiao3_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "傲慢青年",
    "value": "ICL_zh_male_aomanqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "醋精男生",
    "value": "ICL_zh_male_cujingnansheng_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "爽朗少年",
    "value": "ICL_zh_male_shuanglangshaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "撒娇男友",
    "value": "ICL_zh_male_sajiaonanyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "温柔男友",
    "value": "ICL_zh_male_wenrounanyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "温顺少年",
    "value": "ICL_zh_male_wenshunshaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "粘人男友",
    "value": "ICL_zh_male_naigounanyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "撒娇男生",
    "value": "ICL_zh_male_sajiaonansheng_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "活泼男友",
    "value": "ICL_zh_male_huoponanyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "甜系男友",
    "value": "ICL_zh_male_tianxinanyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "活力青年",
    "value": "ICL_zh_male_huoliqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "开朗青年",
    "value": "ICL_zh_male_kailangqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "冷漠兄长",
    "value": "ICL_zh_male_lengmoxiongzhang_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "天才同桌",
    "value": "ICL_zh_male_tiancaitongzhuo_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "翩翩公子",
    "value": "ICL_zh_male_pianpiangongzi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "懵懂青年",
    "value": "ICL_zh_male_mengdongqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "冷脸兄长",
    "value": "ICL_zh_male_lenglianxiongzhang_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "病娇少年",
    "value": "ICL_zh_male_bingjiaoshaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "病娇男友",
    "value": "ICL_zh_male_bingjiaonanyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "病弱少年",
    "value": "ICL_zh_male_bingruoshaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "意气少年",
    "value": "ICL_zh_male_yiqishaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "干净少年",
    "value": "ICL_zh_male_ganjingshaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "冷漠男友",
    "value": "ICL_zh_male_lengmonanyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "精英青年",
    "value": "ICL_zh_male_jingyingqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "热血少年",
    "value": "ICL_zh_male_rexueshaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "清爽少年",
    "value": "ICL_zh_male_qingshuangshaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "中二青年",
    "value": "ICL_zh_male_zhongerqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "凌云青年",
    "value": "ICL_zh_male_lingyunqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "自负青年",
    "value": "ICL_zh_male_zifuqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "不羁青年",
    "value": "ICL_zh_male_bujiqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "儒雅君子",
    "value": "ICL_zh_male_ruyajunzi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "低音沉郁",
    "value": "ICL_zh_male_diyinchenyu_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "冷脸学霸",
    "value": "ICL_zh_male_lenglianxueba_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "儒雅总裁",
    "value": "ICL_zh_male_ruyazongcai_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "深沉总裁",
    "value": "ICL_zh_male_shenchenzongcai_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "小侯爷",
    "value": "ICL_zh_male_xiaohouye_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "孤高公子",
    "value": "ICL_zh_male_gugaogongzi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "仗剑君子",
    "value": "ICL_zh_male_zhangjianjunzi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "温润学者",
    "value": "ICL_zh_male_wenrunxuezhe_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "亲切青年",
    "value": "ICL_zh_male_qinqieqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "温柔学长",
    "value": "ICL_zh_male_wenrouxuezhang_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "高冷总裁",
    "value": "ICL_zh_male_gaolengzongcai_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "冷峻高智",
    "value": "ICL_zh_male_lengjungaozhi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "孱弱少爷",
    "value": "ICL_zh_male_chanruoshaoye_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "自信青年",
    "value": "ICL_zh_male_zixinqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "青涩青年",
    "value": "ICL_zh_male_qingseqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "学霸同桌",
    "value": "ICL_zh_male_xuebatongzhuo_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "冷傲总裁",
    "value": "ICL_zh_male_lengaozongcai_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "元气少年",
    "value": "ICL_zh_male_yuanqishaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "洒脱青年",
    "value": "ICL_zh_male_satuoqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "直率青年",
    "value": "ICL_zh_male_zhishuaiqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "斯文青年",
    "value": "ICL_zh_male_siwenqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "俊逸公子",
    "value": "ICL_zh_male_junyigongzi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "仗剑侠客",
    "value": "ICL_zh_male_zhangjianxiake_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "机甲智能",
    "value": "ICL_zh_male_jijiaozhineng_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "奶气萌娃",
    "value": "zh_male_naiqimengwa_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：剪映同款、豆包同款；对应2.0：奶气萌娃 2.0；MIX：是",
    "tags": "剪映同款、豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "婆婆",
    "value": "zh_female_popo_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：剪映同款、抖音同款、豆包同款；对应2.0：婆婆 2.0；MIX：是",
    "tags": "剪映同款、抖音同款、豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "高冷御姐",
    "value": "zh_female_gaolengyujie_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：高冷御姐 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "傲娇霸总",
    "value": "zh_male_aojiaobazong_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：傲娇霸总 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "魅力女友",
    "value": "zh_female_meilinvyou_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、剪映同款；对应2.0：魅力女友 2.0；MIX：是",
    "tags": "豆包同款、剪映同款"
  },
  {
    "scene": "角色扮演",
    "label": "深夜播客",
    "value": "zh_male_shenyeboke_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：深夜播客 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "柔美女友",
    "value": "zh_female_sajiaonvyou_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、剪映同款；对应2.0：柔美女友 2.0；MIX：是",
    "tags": "豆包同款、剪映同款"
  },
  {
    "scene": "角色扮演",
    "label": "撒娇学妹",
    "value": "zh_female_yuanqinvyou_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、剪映同款；对应2.0：撒娇学妹 2.0；MIX：是",
    "tags": "豆包同款、剪映同款"
  },
  {
    "scene": "角色扮演",
    "label": "病弱少女",
    "value": "ICL_zh_female_bingruoshaonv_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "活泼女孩",
    "value": "ICL_zh_female_huoponvhai_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演",
    "label": "东方浩然",
    "value": "zh_male_dongfanghaoran_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：东方浩然 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "绿茶小哥",
    "value": "ICL_zh_male_lvchaxiaoge_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "娇弱萝莉",
    "value": "ICL_zh_female_jiaoruoluoli_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "冷淡疏离",
    "value": "ICL_zh_male_lengdanshuli_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "憨厚敦实",
    "value": "ICL_zh_male_hanhoudunshi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "活泼刁蛮",
    "value": "ICL_zh_female_huopodiaoman_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "固执病娇",
    "value": "ICL_zh_male_guzhibingjiao_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "撒娇粘人",
    "value": "ICL_zh_male_sajiaonianren_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "傲慢娇声",
    "value": "ICL_zh_female_aomanjiaosheng_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "潇洒随性",
    "value": "ICL_zh_male_xiaosasuixing_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "诡异神秘",
    "value": "ICL_zh_male_guiyishenmi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "儒雅才俊",
    "value": "ICL_zh_male_ruyacaijun_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "正直青年",
    "value": "ICL_zh_male_zhengzhiqingnian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "娇憨女王",
    "value": "ICL_zh_female_jiaohannvwang_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演",
    "label": "病娇萌妹",
    "value": "ICL_zh_female_bingjiaomengmei_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "青涩小生",
    "value": "ICL_zh_male_qingsenaigou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "纯真学弟",
    "value": "ICL_zh_male_chunzhenxuedi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "优柔帮主",
    "value": "ICL_zh_male_youroubangzhu_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "优柔公子",
    "value": "ICL_zh_male_yourougongzi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "调皮公主",
    "value": "ICL_zh_female_tiaopigongzhu_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "贴心男友",
    "value": "ICL_zh_male_tiexinnanyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "少年将军",
    "value": "ICL_zh_male_shaonianjiangjun_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "病娇哥哥",
    "value": "ICL_zh_male_bingjiaogege_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "学霸男同桌",
    "value": "ICL_zh_male_xuebanantongzhuo_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "幽默叔叔",
    "value": "ICL_zh_male_youmoshushu_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "假小子",
    "value": "ICL_zh_female_jiaxiaozi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "温柔男同桌",
    "value": "ICL_zh_male_wenrounantongzhuo_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "幽默大爷",
    "value": "ICL_zh_male_youmodaye_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "枕边低语",
    "value": "ICL_zh_male_asmryexiu_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：抖音同款；MIX：是",
    "tags": "抖音同款"
  },
  {
    "scene": "角色扮演",
    "label": "神秘法师",
    "value": "ICL_zh_male_shenmifashi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "娇喘女声",
    "value": "zh_female_jiaochuan_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、抖音同款；对应2.0：娇喘女声 2.0；MIX：是",
    "tags": "剪映同款、抖音同款"
  },
  {
    "scene": "角色扮演",
    "label": "开朗弟弟",
    "value": "zh_male_livelybro_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、抖音同款；对应2.0：开朗弟弟 2.0；MIX：是",
    "tags": "剪映同款、抖音同款"
  },
  {
    "scene": "角色扮演",
    "label": "谄媚女声",
    "value": "zh_female_flattery_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；标签：剪映同款、抖音同款；对应2.0：谄媚女声 2.0；MIX：是",
    "tags": "剪映同款、抖音同款"
  },
  {
    "scene": "角色扮演",
    "label": "冷峻上司",
    "value": "ICL_zh_male_lengjunshangsi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "寡言小哥",
    "value": "ICL_zh_male_xiaoge_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "清朗温润",
    "value": "ICL_zh_male_renyuwangzi_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "潇洒随性",
    "value": "ICL_zh_male_xiaosha_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "清冷矜贵",
    "value": "ICL_zh_male_liyisheng_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "沉稳优雅",
    "value": "ICL_zh_male_qinglen_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "清逸苏感",
    "value": "ICL_zh_male_chongqingzhanzhan_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "温柔内敛",
    "value": "ICL_zh_male_xingjiwangzi_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "低沉缱绻",
    "value": "ICL_zh_male_sigeshiye_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "蓝银草魂师",
    "value": "ICL_zh_male_lanyingcaohunshi_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "清冷高雅",
    "value": "ICL_zh_female_liumengdie_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "甜美娇俏",
    "value": "ICL_zh_female_linxueying_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "柔骨魂师",
    "value": "ICL_zh_female_rouguhunshi_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "甜美活泼",
    "value": "ICL_zh_female_tianmei_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "成熟温柔",
    "value": "ICL_zh_female_chengshu_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "贴心闺蜜",
    "value": "ICL_zh_female_xnx_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "温柔白月光",
    "value": "ICL_zh_female_yry_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演",
    "label": "高冷沉稳",
    "value": "zh_male_bv139_audiobook_ummv3_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；对应2.0：高冷沉稳 2.0；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "醋精男友",
    "value": "ICL_zh_male_cujingnanyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "风发少年",
    "value": "ICL_zh_male_fengfashaonian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "磁性男嗓",
    "value": "ICL_zh_male_cixingnansang_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "成熟总裁",
    "value": "ICL_zh_male_chengshuzongcai_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "傲娇精英",
    "value": "ICL_zh_male_aojiaojingying_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "傲娇公子",
    "value": "ICL_zh_male_aojiaogongzi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "霸道少爷",
    "value": "ICL_zh_male_badaoshaoye_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "腹黑公子",
    "value": "ICL_zh_male_fuheigongzi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "暖心学姐",
    "value": "ICL_zh_female_nuanxinxuejie_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "可爱女生",
    "value": "ICL_zh_female_keainvsheng_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "成熟姐姐",
    "value": "ICL_zh_female_chengshujiejie_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "病娇姐姐",
    "value": "ICL_zh_female_bingjiaojiejie_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "妩媚御姐",
    "value": "ICL_zh_female_wumeiyujie_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "傲娇女友",
    "value": "ICL_zh_female_aojiaonvyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "贴心女友",
    "value": "ICL_zh_female_tiexinnvyou_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "性感御姐",
    "value": "ICL_zh_female_xingganyujie_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "病娇弟弟",
    "value": "ICL_zh_male_bingjiaodidi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "傲慢少爷",
    "value": "ICL_zh_male_aomanshaoye_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款、猫箱同款；MIX：是",
    "tags": "豆包同款、猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "傲气凌人",
    "value": "ICL_zh_male_aiqilingren_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "角色扮演、S2S-SC",
    "label": "病娇白莲",
    "value": "ICL_zh_male_bingjiaobailian_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：猫箱同款；MIX：是",
    "tags": "猫箱同款"
  },
  {
    "scene": "多语种",
    "label": "Lauren",
    "value": "en_female_lauren_moon_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "EnergeticMaleII",
    "value": "en_male_campaign_jamal_moon_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "GothamHero",
    "value": "en_male_chris_moon_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "FlirtyFemale",
    "value": "en_female_product_darcie_moon_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "PeacefulFemale",
    "value": "en_female_emotional_moon_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Nara",
    "value": "en_female_nara_moon_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Bruce",
    "value": "en_male_bruce_moon_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Michael",
    "value": "en_male_michael_moon_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Cartoon Chef",
    "value": "ICL_en_male_cc_sha_v1_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Lucas",
    "value": "zh_male_M100_conversation_wvae_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Sophie",
    "value": "zh_female_sophie_conversation_wvae_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Daisy",
    "value": "en_female_dacey_conversation_wvae_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Owen",
    "value": "en_male_charlie_conversation_wvae_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Luna",
    "value": "en_female_sarah_new_conversation_wvae_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Michael",
    "value": "ICL_en_male_michael_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Charlie",
    "value": "ICL_en_female_cc_cm_v1_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Big Boogie",
    "value": "ICL_en_male_oogie2_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Frosty Man",
    "value": "ICL_en_male_frosty1_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "The Grinch",
    "value": "ICL_en_male_grinch2_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Zayne",
    "value": "ICL_en_male_zayne_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Jigsaw",
    "value": "ICL_en_male_cc_jigsaw_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Chucky",
    "value": "ICL_en_male_cc_chucky_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Clown Man",
    "value": "ICL_en_male_cc_penny_v1_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Kevin McCallister",
    "value": "ICL_en_male_kevin2_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Xavier",
    "value": "ICL_en_male_xavier1_v1_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Noah",
    "value": "ICL_en_male_cc_dracula_v1_tob",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Adam",
    "value": "en_male_adam_mars_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Amanda",
    "value": "en_female_amanda_mars_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Jackson",
    "value": "en_male_jackson_mars_bigtts",
    "language": "美式英语",
    "capabilities": "",
    "description": "语种/方言：美式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "DelicateGirl",
    "value": "en_female_daisy_moon_bigtts",
    "language": "英式英语",
    "capabilities": "",
    "description": "语种/方言：英式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Dave",
    "value": "en_male_dave_moon_bigtts",
    "language": "英式英语",
    "capabilities": "",
    "description": "语种/方言：英式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Hades",
    "value": "en_male_hades_moon_bigtts",
    "language": "英式英语",
    "capabilities": "",
    "description": "语种/方言：英式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Onez",
    "value": "en_female_onez_moon_bigtts",
    "language": "英式英语",
    "capabilities": "",
    "description": "语种/方言：英式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Emily",
    "value": "en_female_emily_mars_bigtts",
    "language": "英式英语",
    "capabilities": "",
    "description": "语种/方言：英式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Daniel",
    "value": "zh_male_xudong_conversation_wvae_bigtts",
    "language": "英式英语",
    "capabilities": "",
    "description": "语种/方言：英式英语；标签：豆包同款；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "多语种",
    "label": "Alastor",
    "value": "ICL_en_male_cc_alastor_tob",
    "language": "英式英语",
    "capabilities": "",
    "description": "语种/方言：英式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Smith",
    "value": "en_male_smith_mars_bigtts",
    "language": "英式英语",
    "capabilities": "",
    "description": "语种/方言：英式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Anna",
    "value": "en_female_anna_mars_bigtts",
    "language": "英式英语",
    "capabilities": "",
    "description": "语种/方言：英式英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Ethan",
    "value": "ICL_en_male_aussie_v1_tob",
    "language": "澳洲英语",
    "capabilities": "",
    "description": "语种/方言：澳洲英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Sarah",
    "value": "en_female_sarah_mars_bigtts",
    "language": "澳洲英语",
    "capabilities": "",
    "description": "语种/方言：澳洲英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Dryw",
    "value": "en_male_dryw_mars_bigtts",
    "language": "澳洲英语",
    "capabilities": "",
    "description": "语种/方言：澳洲英语；MIX：是"
  },
  {
    "scene": "多语种",
    "label": "Diana",
    "value": "multi_female_maomao_conversation_wvae_bigtts",
    "language": "西语",
    "capabilities": "",
    "description": "语种/方言：西语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "Lucía",
    "value": "multi_male_M100_conversation_wvae_bigtts",
    "language": "西语",
    "capabilities": "",
    "description": "语种/方言：西语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "Sofía",
    "value": "multi_female_sophie_conversation_wvae_bigtts",
    "language": "西语",
    "capabilities": "",
    "description": "语种/方言：西语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "Daníel",
    "value": "multi_male_xudong_conversation_wvae_bigtts",
    "language": "西语",
    "capabilities": "",
    "description": "语种/方言：西语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "ひかる（光）",
    "value": "multi_zh_male_youyoujunzi_moon_bigtts",
    "language": "日语",
    "capabilities": "",
    "description": "语种/方言：日语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "さとみ（智美）",
    "value": "multi_female_sophie_conversation_wvae_bigtts",
    "language": "日语",
    "capabilities": "",
    "description": "语种/方言：日语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "まさお（正男）",
    "value": "multi_male_xudong_conversation_wvae_bigtts",
    "language": "日语",
    "capabilities": "",
    "description": "语种/方言：日语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "つき（月）",
    "value": "multi_female_maomao_conversation_wvae_bigtts",
    "language": "日语",
    "capabilities": "",
    "description": "语种/方言：日语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "あけみ（朱美）",
    "value": "multi_female_gaolengyujie_moon_bigtts",
    "language": "日语",
    "capabilities": "",
    "description": "语种/方言：日语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "かずね（和音）/JavierorÁlvaro",
    "value": "multi_male_jingqiangkanye_moon_bigtts",
    "language": "日语,西语",
    "capabilities": "",
    "description": "语种/方言：日语,西语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "はるこ（晴子）/Esmeralda",
    "value": "multi_female_shuangkuaisisi_moon_bigtts",
    "language": "日语,西语",
    "capabilities": "",
    "description": "语种/方言：日语,西语；MIX：否"
  },
  {
    "scene": "多语种",
    "label": "ひろし（広志）/Roberto",
    "value": "multi_male_wanqudashu_moon_bigtts",
    "language": "日语,西语",
    "capabilities": "",
    "description": "语种/方言：日语,西语；MIX：否"
  },
  {
    "scene": "客服场景",
    "label": "理性圆子",
    "value": "ICL_zh_female_lixingyuanzi_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "清甜桃桃",
    "value": "ICL_zh_female_qingtiantaotao_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "清晰小雪",
    "value": "ICL_zh_female_qingxixiaoxue_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "清甜莓莓",
    "value": "ICL_zh_female_qingtianmeimei_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "开朗婷婷",
    "value": "ICL_zh_female_kailangtingting_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "清新沐沐",
    "value": "ICL_zh_male_qingxinmumu_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：清新沐沐 2.0；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "爽朗小阳",
    "value": "ICL_zh_male_shuanglangxiaoyang_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "清新波波",
    "value": "ICL_zh_male_qingxinbobo_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "温婉珊珊",
    "value": "ICL_zh_female_wenwanshanshan_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：温婉珊珊 2.0；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "甜美小雨",
    "value": "ICL_zh_female_tianmeixiaoyu_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "热情艾娜",
    "value": "ICL_zh_female_reqingaina_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：热情艾娜 2.0；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "甜美小橘",
    "value": "ICL_zh_female_tianmeixiaoju_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "沉稳明仔",
    "value": "ICL_zh_male_chenwenmingzai_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "亲切小卓",
    "value": "ICL_zh_male_qinqiexiaozhuo_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "灵动欣欣",
    "value": "ICL_zh_female_lingdongxinxin_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "乖巧可儿",
    "value": "ICL_zh_female_guaiqiaokeer_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "暖心茜茜",
    "value": "ICL_zh_female_nuanxinqianqian_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "软萌团子",
    "value": "ICL_zh_female_ruanmengtuanzi_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "阳光洋洋",
    "value": "ICL_zh_male_yangguangyangyang_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "软萌糖糖",
    "value": "ICL_zh_female_ruanmengtangtang_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "秀丽倩倩",
    "value": "ICL_zh_female_xiuliqianqian_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "开心小鸿",
    "value": "ICL_zh_female_kaixinxiaohong_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "轻盈朵朵",
    "value": "ICL_zh_female_qingyingduoduo_cs_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：轻盈朵朵 2.0；MIX：是"
  },
  {
    "scene": "客服场景",
    "label": "暖阳女声",
    "value": "zh_female_kefunvsheng_mars_bigtts",
    "language": "仅中文",
    "capabilities": "",
    "description": "语种/方言：仅中文；对应2.0：暖阳女声 2.0；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "悠悠君子",
    "value": "zh_male_M100_conversation_wvae_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：悠悠君子 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "视频配音",
    "label": "文静毛毛",
    "value": "zh_female_maomao_conversation_wvae_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：文静毛毛 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "视频配音",
    "label": "倾心少女",
    "value": "ICL_zh_female_qiuling_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "醇厚低音",
    "value": "ICL_zh_male_buyan_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "咆哮小哥",
    "value": "ICL_zh_male_BV144_paoxiaoge_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "和蔼奶奶",
    "value": "ICL_zh_female_heainainai_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "邻居阿姨",
    "value": "ICL_zh_female_linjuayi_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "温柔小雅",
    "value": "zh_female_wenrouxiaoya_moon_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：豆包同款；对应2.0：温柔小雅 2.0；MIX：是",
    "tags": "豆包同款"
  },
  {
    "scene": "视频配音",
    "label": "天才童声",
    "value": "zh_male_tiancaitongsheng_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：天才童声 2.0；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "猴哥",
    "value": "zh_male_sunwukong_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：猴哥 2.0；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "熊二",
    "value": "zh_male_xionger_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：抖音同款、剪映同款、豆包同款；对应2.0：熊二 2.0；MIX：是",
    "tags": "抖音同款、剪映同款、豆包同款"
  },
  {
    "scene": "视频配音",
    "label": "佩奇猪",
    "value": "zh_female_peiqi_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：抖音同款、剪映同款、豆包同款；对应2.0：佩奇猪 2.0；MIX：是",
    "tags": "抖音同款、剪映同款、豆包同款"
  },
  {
    "scene": "视频配音",
    "label": "武则天",
    "value": "zh_female_wuzetian_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：剪映同款；对应2.0：武则天 2.0；MIX：是",
    "tags": "剪映同款"
  },
  {
    "scene": "视频配音",
    "label": "顾姐",
    "value": "zh_female_gujie_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：抖音同款、剪映同款；对应2.0：顾姐 2.0；MIX：是",
    "tags": "抖音同款、剪映同款"
  },
  {
    "scene": "视频配音",
    "label": "樱桃丸子",
    "value": "zh_female_yingtaowanzi_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：剪映同款、抖音同款、豆包同款；对应2.0：樱桃丸子 2.0；MIX：是",
    "tags": "剪映同款、抖音同款、豆包同款"
  },
  {
    "scene": "视频配音",
    "label": "广告解说",
    "value": "zh_male_chunhui_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：剪映同款；对应2.0：广告解说 2.0；MIX：是",
    "tags": "剪映同款"
  },
  {
    "scene": "视频配音",
    "label": "少儿故事",
    "value": "zh_female_shaoergushi_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：少儿故事 2.0；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "四郎",
    "value": "zh_male_silang_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：抖音同款、剪映同款、豆包同款；对应2.0：四郎 2.0；MIX：是",
    "tags": "抖音同款、剪映同款、豆包同款"
  },
  {
    "scene": "视频配音",
    "label": "俏皮女声",
    "value": "zh_female_qiaopinvsheng_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：俏皮女声 2.0；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "懒音绵宝",
    "value": "zh_male_lanxiaoyang_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：懒音绵宝 2.0；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "亮嗓萌仔",
    "value": "zh_male_dongmanhaimian_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：亮嗓萌仔 2.0；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "磁性解说男声/Morgan",
    "value": "zh_male_jieshuonansheng_mars_bigtts",
    "language": "中文,美式英语",
    "capabilities": "",
    "description": "语种/方言：中文,美式英语；标签：抖音同款、剪映同款；对应2.0：磁性解说男声/Morgan 2.0；MIX：是",
    "tags": "抖音同款、剪映同款"
  },
  {
    "scene": "视频配音",
    "label": "鸡汤妹妹/Hope",
    "value": "zh_female_jitangmeimei_mars_bigtts",
    "language": "中文,美式英语",
    "capabilities": "",
    "description": "语种/方言：中文,美式英语；标签：抖音同款、豆包同款；对应2.0：鸡汤妹妹/Hope 2.0；MIX：是",
    "tags": "抖音同款、豆包同款"
  },
  {
    "scene": "视频配音",
    "label": "贴心女声/Candy",
    "value": "zh_female_tiexinnvsheng_mars_bigtts",
    "language": "中文,美式英语",
    "capabilities": "",
    "description": "语种/方言：中文,美式英语；对应2.0：贴心女声/Candy 2.0；MIX：是"
  },
  {
    "scene": "视频配音",
    "label": "萌丫头/Cutey",
    "value": "zh_female_mengyatou_mars_bigtts",
    "language": "中文,美式英语",
    "capabilities": "",
    "description": "语种/方言：中文,美式英语；对应2.0：萌丫头/Cutey 2.0；MIX：是"
  },
  {
    "scene": "有声阅读",
    "label": "内敛才俊",
    "value": "ICL_zh_male_neiliancaijun_e991be511569_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "有声阅读",
    "label": "温暖少年",
    "value": "ICL_zh_male_yangyang_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "有声阅读",
    "label": "儒雅公子",
    "value": "ICL_zh_male_flc_v1_tob",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；MIX：是"
  },
  {
    "scene": "有声阅读",
    "label": "悬疑解说",
    "value": "zh_male_changtianyi_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：剪映同款、抖音同款、豆包同款；对应2.0：悬疑解说 2.0；MIX：是",
    "tags": "剪映同款、抖音同款、豆包同款"
  },
  {
    "scene": "有声阅读",
    "label": "儒雅青年",
    "value": "zh_male_ruyaqingnian_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：番茄小说同款、豆包同款、剪映同款；对应2.0：儒雅青年 2.0；MIX：是",
    "tags": "番茄小说同款、豆包同款、剪映同款"
  },
  {
    "scene": "有声阅读",
    "label": "霸气青叔",
    "value": "zh_male_baqiqingshu_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：番茄小说同款、豆包同款、剪映同款；对应2.0：霸气青叔 2.0；MIX：是",
    "tags": "番茄小说同款、豆包同款、剪映同款"
  },
  {
    "scene": "有声阅读",
    "label": "擎苍",
    "value": "zh_male_qingcang_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：番茄小说同款、剪映同款、豆包同款、抖音同款；对应2.0：擎苍 2.0；MIX：是",
    "tags": "番茄小说同款、剪映同款、豆包同款、抖音同款"
  },
  {
    "scene": "有声阅读",
    "label": "活力小哥",
    "value": "zh_male_yangguangqingnian_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：活力小哥 2.0；MIX：是"
  },
  {
    "scene": "有声阅读",
    "label": "古风少御",
    "value": "zh_female_gufengshaoyu_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：古风少御 2.0；MIX：是"
  },
  {
    "scene": "有声阅读",
    "label": "温柔淑女",
    "value": "zh_female_wenroushunv_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；标签：番茄小说同款、豆包同款、剪映同款；对应2.0：温柔淑女 2.0；MIX：是",
    "tags": "番茄小说同款、豆包同款、剪映同款"
  },
  {
    "scene": "有声阅读",
    "label": "反卷青年",
    "value": "zh_male_fanjuanqingnian_mars_bigtts",
    "language": "中文",
    "capabilities": "",
    "description": "语种/方言：中文；对应2.0：反卷青年 2.0；MIX：是"
  }
];

export const HUOSHAN_TTS_SUPPORTED_VOICES = HUOSHAN_TTS_VOICE_OPTIONS.map((item) => item.value);

export const HUOSHAN_TTS_VOICE_META: Record<string, { label?: string; description?: string }> =
  Object.fromEntries(
    HUOSHAN_TTS_VOICE_OPTIONS.map((item) => [
      item.value,
      { label: item.label, description: item.description },
    ])
  );

export const DEFAULT_TTS_VOICE = "zh_female_qingxinnvsheng_mars_bigtts";
